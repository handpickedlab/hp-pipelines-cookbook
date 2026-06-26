"""Gedeelde modellen, LLM-setup en agent-nodes voor L1–L3."""

from __future__ import annotations

import json
import operator
import os
import time
from typing import Annotated

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from inputs import OUTPUT_PREFERENCES

MAX_ITERATIONS = 3


class Article(BaseModel):
    title: str = Field(description="Pakkende titel van het artikel")
    body_markdown: str = Field(description="Volledige artikeltekst in markdown")


class ReviewResult(BaseModel):
    pass_: bool = Field(alias="pass", description="True als het artikel goed genoeg is")
    reason: str = Field(description="Korte motivatie voor pass/fail")

    model_config = {"populate_by_name": True}


class DraftRecord(TypedDict):
    iteration: int
    stage: str
    title: str
    body_markdown: str
    word_count: int


class ReviewRecord(TypedDict):
    iteration: int
    pass_: bool
    reason: str


class TraceRecord(TypedDict, total=False):
    node: str
    iteration: int
    input: dict
    output: dict
    duration_ms: int
    tokens_in: int
    tokens_out: int
    tokens_total: int
    model: str


class BasePipelineState(TypedDict):
    briefing: str
    preferences: dict
    article: Article
    drafts: Annotated[list[DraftRecord], operator.add]
    reviews: Annotated[list[ReviewRecord], operator.add]
    trace: Annotated[list[TraceRecord], operator.add]
    iteration: int
    revision_notes: str
    review: ReviewResult | None


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


def build_llm() -> ChatOpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY ontbreekt. Kopieer .env.example naar .env "
            "en vul je OpenAI-key in."
        )
    model = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")
    kwargs = {"model": model, "api_key": api_key}
    # gpt-5 / o-serie zijn reasoning-modellen en accepteren geen custom temperature
    # (alleen de default). Alleen voor oudere modellen (gpt-4o etc.) zetten we 'm.
    if not (model.startswith("gpt-5") or model.startswith("o")):
        kwargs["temperature"] = 0.7
    return ChatOpenAI(**kwargs)


def word_count(text: str) -> int:
    return len(text.split())


def must_avoid_violations(body: str, preferences: dict | None = None) -> list[str]:
    prefs = preferences or OUTPUT_PREFERENCES
    lowered = body.lower()
    violations = [
        term
        for term in prefs["must_avoid"]
        if term != "em-dashes" and term in lowered
    ]
    if "—" in body:
        violations.append("em-dash (—)")
    return violations


def draft_record(article: Article, iteration: int, stage: str) -> DraftRecord:
    return {
        "iteration": iteration,
        "stage": stage,
        "title": article.title,
        "body_markdown": article.body_markdown,
        "word_count": word_count(article.body_markdown),
    }


def preferences_block(preferences: dict) -> str:
    return json.dumps(preferences, ensure_ascii=False, indent=2)


def invoke_structured(llm, schema, messages) -> tuple:
    """Roep het model aan met structured output en meet duur + token-gebruik.

    Geeft (parsed_object, meta) terug. `meta` bevat duration_ms en token-counts
    (None als het model die niet meegeeft). Gebruikt include_raw zodat we naast het
    geparste object ook de ruwe AIMessage met usage_metadata in handen krijgen.
    """
    structured = llm.with_structured_output(schema, include_raw=True)
    start = time.perf_counter()
    result = structured.invoke(messages)
    duration_ms = round((time.perf_counter() - start) * 1000)

    parsed = result["parsed"] if isinstance(result, dict) else result
    raw = result.get("raw") if isinstance(result, dict) else None
    usage = getattr(raw, "usage_metadata", None) or {}
    response_meta = getattr(raw, "response_metadata", None) or {}

    meta = {
        "duration_ms": duration_ms,
        "tokens_in": usage.get("input_tokens"),
        "tokens_out": usage.get("output_tokens"),
        "tokens_total": usage.get("total_tokens"),
        "model": response_meta.get("model_name"),
    }
    return parsed, meta


def writer_node(state: BasePipelineState) -> dict:
    llm = build_llm()

    revision = state.get("revision_notes", "").strip()
    revision_block = f"\n\nREVISIE-OPDRACHT:\n{revision}" if revision else ""

    user_prompt = (
        f"BRIEFING:\n{state['briefing']}\n\n"
        f"OUTPUT PREFERENCES (JSON):\n{preferences_block(state['preferences'])}"
        f"{revision_block}"
    )

    article, meta = invoke_structured(
        llm, Article, [("system", WRITER_SYSTEM), ("user", user_prompt)]
    )
    iteration = state.get("iteration", 1)

    return {
        "article": article,
        "drafts": [draft_record(article, iteration, "writer")],
        "trace": [
            {
                "node": "writer",
                "iteration": iteration,
                "input": {"system": WRITER_SYSTEM, "user": user_prompt},
                "output": article.model_dump(),
                **meta,
            }
        ],
    }


def editor_node(state: BasePipelineState) -> dict:
    llm = build_llm()
    article = state["article"]
    iteration = state.get("iteration", 1)

    user_prompt = (
        f"BRIEFING:\n{state['briefing']}\n\n"
        f"OUTPUT PREFERENCES (JSON):\n{preferences_block(state['preferences'])}\n\n"
        f"HUIDIGE DRAFT:\nTitel: {article.title}\n\n{article.body_markdown}"
    )

    edited, meta = invoke_structured(
        llm, Article, [("system", EDITOR_SYSTEM), ("user", user_prompt)]
    )

    return {
        "article": edited,
        "drafts": [draft_record(edited, iteration, "editor")],
        "trace": [
            {
                "node": "editor",
                "iteration": iteration,
                "input": {"system": EDITOR_SYSTEM, "user": user_prompt},
                "output": edited.model_dump(),
                **meta,
            }
        ],
    }


def reviewer_node(state: BasePipelineState) -> dict:
    llm = build_llm()
    article = state["article"]
    iteration = state.get("iteration", 1)
    wc = word_count(article.body_markdown)

    user_prompt = (
        f"BRIEFING:\n{state['briefing']}\n\n"
        f"OUTPUT PREFERENCES (JSON):\n{preferences_block(state['preferences'])}\n\n"
        f"ARTIKEL:\nTitel: {article.title}\n\n{article.body_markdown}\n\n"
        f"Woorden (geteld): {wc}"
    )

    review, meta = invoke_structured(
        llm, ReviewResult, [("system", REVIEWER_SYSTEM), ("user", user_prompt)]
    )
    target = state["preferences"]["length_words"]
    low, high = round(target * 0.9), round(target * 1.1)
    violations = must_avoid_violations(article.body_markdown, state["preferences"])
    local_failures: list[str] = []
    if not low <= wc <= high:
        local_failures.append(f"lengte {wc} woorden valt buiten marge {low}-{high}")
    if violations:
        local_failures.append(f"must_avoid overtredingen: {', '.join(violations)}")
    if local_failures:
        reason = "; ".join(local_failures)
        review = ReviewResult(pass_=False, reason=f"Lokale validatie faalt: {reason}.")

    return {
        "review": review,
        "reviews": [
            {
                "iteration": iteration,
                "pass_": review.pass_,
                "reason": review.reason,
            }
        ],
        "trace": [
            {
                "node": "reviewer",
                "iteration": iteration,
                "input": {"system": REVIEWER_SYSTEM, "user": user_prompt},
                "output": review.model_dump(by_alias=True),
                **meta,
            }
        ],
    }


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
