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

Vul na een run de cel in voor PydanticAI (verdict + setup-tijd, highs, lows, effort), zodat
de vergelijking met `langgraph` compleet wordt.
