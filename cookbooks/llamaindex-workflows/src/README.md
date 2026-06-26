# LlamaIndex Workflows — writer-benchmark

LlamaIndex Workflows-implementatie van de **vaste schrijf-casus**: Writer → Editor →
Reviewer → Orchestrator (revisie-loop) → HITL. Python + OpenAI. Drie oplopende niveaus,
dezelfde input elke run — zodat het framework de enige variabele is t.o.v. de andere
cookbooks (`langgraph`, `pydanticai`).

> De casus (briefing + output-preferences) staat in [`inputs.py`](inputs.py) en is identiek
> aan de andere framework-cookbooks. Pas die niet aan voor een eerlijke vergelijking.

## Niveaus

| Niveau | Bestand | Wat draait |
|---|---|---|
| **L1** Writer | `l1_writer.py` | Workflow met één step (structured output via `as_structured_llm`) |
| **L2** Lineaire chain | `l2_chain.py` | Workflow: write → edit → review, state reist mee in events |
| **L3** Orchestrator + HITL | `l3_orchestrator.py` | Workflow met revisie-loop (max 3) + `InputRequiredEvent`/`HumanResponseEvent` |

## Setup

```bash
cp .env.example .env        # vul OPENAI_API_KEY in
```

OpenAI-key via [platform.openai.com](https://platform.openai.com/api-keys). Model
overridebaar via `OPENAI_MODEL` (default `gpt-5.4-mini`).

## Runnen — CLI

```bash
./start.sh                  # L1 (default)
./start.sh l2               # write → edit → review
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
observability-kaart (LLM-calls, latency, tokens via `TokenCountingHandler`).

## Structuur

- `inputs.py` — vaste briefing + output preferences (de casus).
- `common.py` — modellen, prompts, de lokale validatie-gate, de LlamaIndex LLM-laag
  (`as_structured_llm` + `TokenCountingHandler`) en de `writer/editor/reviewer`-steps; plus
  `ui_payload` (zelfde shape als de andere cookbooks).
- `l1_writer.py` / `l2_chain.py` / `l3_orchestrator.py` — een `Workflow` + `generate()` per
  niveau + CLI-runner.
- `api/index.py` + `api/_ui.py` — de serverless web-UI.
- `middleware.ts` / `vercel.json` — wachtwoord-gate en routing voor de Vercel-deploy.

## L3 — events, loop, HITL & checkpointing

L3 is een echte Workflow: `generate` (write→edit→review) → `decide`. Bij een fail loopt een
`GenerateEvent` terug (loop, guard op max 3). Bij een pass schrijft de Workflow een
**`InputRequiredEvent`** naar de stream en wacht via `ctx.wait_for_event` op een
**`HumanResponseEvent`**; de runner (CLI of web-auto-approve) beantwoordt die. De Reviewer
heeft dezelfde **lokale validatie-gate** als de andere cookbooks.

Dit is een sterk punt van Workflows in de benchmark: HITL is **ingebouwd** (events), en met
`WorkflowCheckpointer` is resume-na-pauze mogelijk — waar PydanticAI dat handmatig moet
wiren.

## Findings

Vul na een run de cel in voor LlamaIndex Workflows (verdict + setup-tijd, highs, lows,
effort), zodat de vergelijking met `langgraph` en `pydanticai` compleet wordt.
