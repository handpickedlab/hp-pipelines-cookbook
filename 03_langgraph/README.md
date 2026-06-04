# 03 — LangGraph

LangGraph-implementatie van de vaste casus (zie [root README](../README.md)). Python + Gemini.

## Status

| Niveau | Bestand | Status |
|---|---|---|
| **L1** Writer | `l1_writer.py` | ✅ |
| **L2** Lineaire chain | `l2_chain.py` | ✅ |
| **L3** Orchestrator + HITL | `l3_orchestrator.py` | ✅ |

## Setup

```bash
cp .env.example .env        # vul GOOGLE_GENERATIVE_AI_API_KEY in
```

Gemini-key haal je bij [Google AI Studio](https://aistudio.google.com/apikey).

## Runnen

```bash
./start.sh                  # L1 (default)
./start.sh l2               # Writer → Editor → Reviewer
./start.sh l3               # revisie-loop + HITL prompt in terminal
./start.sh l3 --auto-approve      # L3 smoke test zonder HITL prompt
```

Of handmatig:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python l2_chain.py
python l3_orchestrator.py --auto-approve
```

## Structuur

- `inputs.py` — vaste briefing + output preferences (identiek aan root README).
- `common.py` — gedeelde modellen, LLM-setup en Writer/Editor/Reviewer nodes.
- `l1_writer.py` — één Writer-node.
- `l2_chain.py` — lineaire chain; print JSON UI-payload na afloop.
- `l3_orchestrator.py` — revisie-loop (max 3 iteraties), checkpointing, HITL via `interrupt()`.

## L3 — HITL & checkpointing

Na een geslaagde review pauzeert de graph bij de `hitl`-node. In de terminal kies je goedkeuring of stuur je terug met feedback. De run hervat via checkpointing (`InMemorySaver`) zonder opnieuw te starten.

Voor geautomatiseerde runs: `--auto-approve`.

## Findings

Vul na het draaien de cel in de [vergelijkingsmatrix](../README.md#vergelijkingsmatrix) en gebruik de findings-template onderaan de root README.
