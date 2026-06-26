# PydanticAI — writer-benchmark

PydanticAI-implementatie van de **vaste schrijf-casus**: Writer → Editor → Reviewer →
Orchestrator (revisie-loop) → HITL. Python + OpenAI. Drie oplopende niveaus, dezelfde
input elke run — zodat het framework de enige variabele is t.o.v. de andere cookbooks
(`langgraph`, …).

> De casus (briefing + output-preferences) staat in [`inputs.py`](inputs.py) en is identiek
> aan de andere framework-cookbooks. Pas die niet aan voor een eerlijke vergelijking.

## Niveaus

| Niveau | Bestand | Wat draait |
|---|---|---|
| **L1** Writer | `l1_writer.py` | één Writer-agent (`output_type=Article`) |
| **L2** Lineaire chain | `l2_chain.py` | Writer → Editor → Reviewer |
| **L3** Orchestrator + HITL | `l3_orchestrator.py` | revisie-loop (max 3) + HITL |

## Setup

```bash
cp .env.example .env        # vul OPENAI_API_KEY in
```

OpenAI-key via [platform.openai.com](https://platform.openai.com/api-keys). Model
overridebaar via `OPENAI_MODEL` (default `gpt-5.4-mini`).

## Runnen — CLI

```bash
./start.sh                  # L1 (default)
./start.sh l2               # Writer → Editor → Reviewer
./start.sh l3               # revisie-loop + HITL prompt in terminal
./start.sh l3 -- --auto-approve   # L3 zonder HITL-prompt
```

## Runnen — web-UI (serverless)

```bash
pip install -r requirements.txt uvicorn
uvicorn api.index:app --reload      # http://localhost:8000
```

Op Vercel staat dit als serverless function achter de wachtwoord-gate (zie `HOSTING.md`).
De UI heeft een input-paneel (briefing + preferences, voorgevuld met de vaste casus) en een
observability-kaart (LLM-calls, latency, tokens per run via `result.usage()`). Zet
`LOGFIRE_TOKEN` (+ `logfire` in requirements) voor volledige traces in Pydantic Logfire.

## Structuur

- `inputs.py` — vaste briefing + output preferences (de casus).
- `common.py` — modellen, prompts, de lokale validatie-gate, de PydanticAI-agents en de
  `writer/editor/reviewer`-steps; plus `ui_payload` (zelfde shape als de andere cookbooks).
- `l1_writer.py` / `l2_chain.py` / `l3_orchestrator.py` — `generate()` per niveau + CLI-runner.
- `api/index.py` + `api/_ui.py` — de serverless web-UI.
- `middleware.ts` / `vercel.json` — wachtwoord-gate en routing voor de Vercel-deploy.

## L3 — loop, HITL & geen checkpointing

De revisie-loop (max 3) is plain Python: Writer→Editor→Reviewer, en bij een geslaagde
review een HITL-beslissing (CLI: terminal-prompt; web: auto-approve). De Reviewer heeft
dezelfde **lokale validatie-gate** als de andere cookbooks (lengte + must_avoid →
deterministisch `pass=false`).

Anders dan LangGraph kent PydanticAI **geen ingebouwde checkpointing/interrupt** voor deze
flow; resume-na-pauze zou je zelf moeten bouwen (bv. via `pydantic_graph`-persistence). Dat
is meteen een benchmark-finding: orkestratie + HITL wire je hier handmatig.

## Findings

Gemeten op **`gpt-5.4-mini`**. Mechaniek van L1/L2/L3 geverifieerd; L3 end-to-end gedraaid.

**L1/L2** ✅ — Agents met `output_type` geven structured output zonder gedoe; `result.usage()`
levert tokens voor de observability. Lineaire L2 is gewoon drie sequentiële `run_sync`-calls.

**L3** ⚠️ — De revisie-loop + guard werken (plain-Python orkestratie), maar in de testrun
**schoot het model de lengte over** (692 → 812 → 802 woorden, target 540-660) en haalde nooit
een pass → gestopt op `max_iterations_reached`. Contrast met `langgraph`, dat met hetzelfde
model/casus wél convergeerde (670 → 601, pass op iter 2). Eén stochastische run, dus
voorzichtig — maar het laat zien dat deze casus gevoelig is voor framework/prompt-gedrag op
de lengte-constraint.

**Lows 👎** — PydanticAI heeft **geen ingebouwde checkpointing/interrupt** voor de L3-loop;
HITL + resume wire je handmatig (vs. LangGraph's `interrupt()`/checkpointing en LlamaIndex'
`InputRequiredEvent`/`WorkflowCheckpointer`). Effort: laag voor L1/L2, medium voor L3.
