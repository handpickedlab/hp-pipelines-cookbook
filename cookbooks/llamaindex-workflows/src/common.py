"""Gedeelde modellen, LLM-laag en pipeline-steps voor L1–L3 (LlamaIndex Workflows).

De casus (briefing/preferences, prompts, validatie-gate, ui_payload) is identiek aan de
andere framework-cookbooks; alleen de uitvoeringslaag is LlamaIndex Workflows. De steps
vullen dezelfde state-shape zodat `ui_payload` ongewijzigd werkt.
"""

from __future__ import annotations

import json
import os
import time

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, Field

from inputs import OUTPUT_PREFERENCES

MAX_ITERATIONS = 3


# --- Casus-modellen (framework-agnostisch) -------------------------------------

class Article(BaseModel):
    title: str = Field(description="Pakkende titel van het artikel")
    body_markdown: str = Field(description="Volledige artikeltekst in markdown")


class ReviewResult(BaseModel):
    pass_: bool = Field(alias="pass", description="True als het artikel goed genoeg is")
    reason: str = Field(description="Korte motivatie voor pass/fail")

    model_config = {"populate_by_name": True}


WRITER_SYSTEM = """Je bent een ervaren B2B-copywriter die in het Nederlands schrijft.
Schrijf een LinkedIn-artikel dat exact voldoet aan de output preferences.

Harde regels:
- Houd je aan length_words (richtlijn, ruim binnen ±10%).
- Volg de structure-volgorde.
- Verwerk alles uit must_include.
- Gebruik NOOIT iets uit must_avoid. Geen em-dashes (—), gebruik gewone komma's of punten.
- Toon: zoals beschreven in 'tone'. Geloofwaardig en zelfverzekerd, geen marketinghype.
"""

EDITOR_SYSTEM = """Je bent een senior editor voor B2B LinkedIn-content in het Nederlands.
Verbeter structuur, lengte, leesbaarheid en handhaaf de output preferences.

Harde regels:
- Houd length_words aan (±10%).
- Behoud must_include; verwijder must_avoid-termen en em-dashes (—).
- Verbeter hook, flow en call-to-action zonder hype.
- Lever het volledige herschreven artikel terug, geen commentaar buiten het artikel.
"""

REVIEWER_SYSTEM = """Je bent een strenge redacteur. Beoordeel het artikel tegen briefing en output preferences.
Geef pass=true alleen als lengte, structuur, must_include en must_avoid in orde zijn.
Wees concreet in reason bij pass=false: noem wat ontbreekt of fout is.
"""


# --- Validatie-gate + helpers (framework-agnostisch) ---------------------------

def word_count(text: str) -> int:
    return len(text.split())


def must_avoid_violations(body: str, preferences: dict | None = None) -> list[str]:
    prefs = preferences or OUTPUT_PREFERENCES
    lowered = body.lower()
    violations = [
        term for term in prefs["must_avoid"] if term != "em-dashes" and term in lowered
    ]
    if "—" in body:
        violations.append("em-dash (—)")
    return violations


def draft_record(article: Article, iteration: int, stage: str) -> dict:
    return {
        "iteration": iteration,
        "stage": stage,
        "title": article.title,
        "body_markdown": article.body_markdown,
        "word_count": word_count(article.body_markdown),
    }


def preferences_block(preferences: dict) -> str:
    return json.dumps(preferences, ensure_ascii=False, indent=2)


def initial_state(briefing: str, preferences: dict) -> dict:
    return {
        "briefing": briefing,
        "preferences": preferences,
        "drafts": [],
        "reviews": [],
        "trace": [],
        "iteration": 1,
        "revision_notes": "",
        "review": None,
    }


LIST_KEYS = ("drafts", "reviews", "trace")


def apply_update(state: dict, update: dict) -> None:
    for key, value in update.items():
        if key in LIST_KEYS:
            state.setdefault(key, []).extend(value)
        else:
            state[key] = value


# --- LlamaIndex LLM-laag + token-counting --------------------------------------

def current_model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")


def build_llm_and_counter() -> tuple:
    """OpenAI-LLM met een TokenCountingHandler eraan gekoppeld voor observability."""
    model = current_model()
    token_counter = TokenCountingHandler()
    # gpt-5 / o-serie zijn reasoning-modellen en accepteren alleen de default
    # temperature (1.0); oudere modellen (gpt-4o etc.) krijgen 0.7.
    temperature = 1.0 if (model.startswith("gpt-5") or model.startswith("o")) else 0.7
    llm = OpenAI(
        model=model,
        temperature=temperature,
        callback_manager=CallbackManager([token_counter]),
    )
    return llm, token_counter


async def run_structured(llm, token_counter, system: str, user: str, output_model) -> tuple:
    """Eén structured LLM-call; geeft (parsed, meta) terug met duur + tokens."""
    sllm = llm.as_structured_llm(output_model)
    token_counter.reset_counts()
    start = time.perf_counter()
    resp = await sllm.achat(
        [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)]
    )
    duration_ms = round((time.perf_counter() - start) * 1000)

    parsed = getattr(resp, "raw", None)
    if not isinstance(parsed, output_model):
        parsed = output_model.model_validate_json(resp.message.content)

    meta = {
        "duration_ms": duration_ms,
        "tokens_in": token_counter.prompt_llm_token_count or None,
        "tokens_out": token_counter.completion_llm_token_count or None,
        "tokens_total": token_counter.total_llm_token_count or None,
        "model": current_model(),
    }
    return parsed, meta


# --- Pipeline-steps (gedeeld door alle niveaus) --------------------------------

async def writer_step(state: dict, llm, token_counter) -> dict:
    revision = state.get("revision_notes", "").strip()
    revision_block = f"\n\nREVISIE-OPDRACHT:\n{revision}" if revision else ""
    user = (
        f"BRIEFING:\n{state['briefing']}\n\n"
        f"OUTPUT PREFERENCES (JSON):\n{preferences_block(state['preferences'])}"
        f"{revision_block}"
    )
    article, meta = await run_structured(llm, token_counter, WRITER_SYSTEM, user, Article)
    iteration = state.get("iteration", 1)
    return {
        "article": article,
        "drafts": [draft_record(article, iteration, "writer")],
        "trace": [{"node": "writer", "iteration": iteration, **meta}],
    }


async def editor_step(state: dict, llm, token_counter) -> dict:
    article = state["article"]
    iteration = state.get("iteration", 1)
    user = (
        f"BRIEFING:\n{state['briefing']}\n\n"
        f"OUTPUT PREFERENCES (JSON):\n{preferences_block(state['preferences'])}\n\n"
        f"HUIDIGE DRAFT:\nTitel: {article.title}\n\n{article.body_markdown}"
    )
    edited, meta = await run_structured(llm, token_counter, EDITOR_SYSTEM, user, Article)
    return {
        "article": edited,
        "drafts": [draft_record(edited, iteration, "editor")],
        "trace": [{"node": "editor", "iteration": iteration, **meta}],
    }


async def reviewer_step(state: dict, llm, token_counter) -> dict:
    article = state["article"]
    iteration = state.get("iteration", 1)
    wc = word_count(article.body_markdown)
    user = (
        f"BRIEFING:\n{state['briefing']}\n\n"
        f"OUTPUT PREFERENCES (JSON):\n{preferences_block(state['preferences'])}\n\n"
        f"ARTIKEL:\nTitel: {article.title}\n\n{article.body_markdown}\n\n"
        f"Woorden (geteld): {wc}"
    )
    review, meta = await run_structured(llm, token_counter, REVIEWER_SYSTEM, user, ReviewResult)

    target = state["preferences"]["length_words"]
    low, high = round(target * 0.9), round(target * 1.1)
    violations = must_avoid_violations(article.body_markdown, state["preferences"])
    local_failures: list[str] = []
    if not low <= wc <= high:
        local_failures.append(f"lengte {wc} woorden valt buiten marge {low}-{high}")
    if violations:
        local_failures.append(f"must_avoid overtredingen: {', '.join(violations)}")
    if local_failures:
        review = ReviewResult(pass_=False, reason=f"Lokale validatie faalt: {'; '.join(local_failures)}.")

    return {
        "review": review,
        "reviews": [{"iteration": iteration, "pass_": review.pass_, "reason": review.reason}],
        "trace": [{"node": "reviewer", "iteration": iteration, **meta}],
    }


# --- Output-payload voor de UI (framework-agnostisch) --------------------------

def ui_payload(result: dict, *, level: str, extra: dict | None = None) -> dict:
    article: Article = result["article"]
    body = article.body_markdown
    target = result["preferences"]["length_words"]
    low, high = round(target * 0.9), round(target * 1.1)
    wc = word_count(body)

    payload = {
        "level": level,
        "final_copy": {
            "title": article.title,
            "body_markdown": body,
            "word_count": wc,
            "within_length_target": low <= wc <= high,
        },
        "drafts": result.get("drafts", []),
        "reviews": [
            {"iteration": r["iteration"], "pass": r["pass_"], "reason": r["reason"]}
            for r in result.get("reviews", [])
        ],
        "iteration_count": result.get("iteration", 1),
        "must_avoid_violations": must_avoid_violations(body, result["preferences"]),
        "trace_nodes": [t["node"] for t in result.get("trace", [])],
        "trace": [
            {
                "node": t.get("node"),
                "iteration": t.get("iteration"),
                "duration_ms": t.get("duration_ms"),
                "tokens_in": t.get("tokens_in"),
                "tokens_out": t.get("tokens_out"),
                "tokens_total": t.get("tokens_total"),
            }
            for t in result.get("trace", [])
        ],
        "totals": _trace_totals(result.get("trace", [])),
    }
    if extra:
        payload.update(extra)
    return payload


def _trace_totals(trace: list) -> dict:
    def _sum(key: str):
        vals = [t.get(key) for t in trace if isinstance(t.get(key), (int, float))]
        return sum(vals) if vals else None

    return {
        "llm_calls": len(trace),
        "duration_ms": _sum("duration_ms"),
        "tokens_in": _sum("tokens_in"),
        "tokens_out": _sum("tokens_out"),
        "tokens_total": _sum("tokens_total"),
    }
