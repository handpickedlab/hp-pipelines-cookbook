# HOSTING — LangGraph (writer-benchmark)

`runtime: none` — dit cookbook wordt **niet gedeployd**. Het is een lokaal te draaien
Python-experiment (CLI); de catalogus linkt naar de bestanden in `src/`. Er is geen
Vercel-project en geen `url:` in het manifest.

## Lokaal draaien

```bash
cd src
cp .env.example .env        # vul OPENAI_API_KEY in
./start.sh                  # L1 (default)
./start.sh l2               # Writer → Editor → Reviewer
./start.sh l3               # revisie-loop + HITL prompt in terminal
./start.sh l3 -- --auto-approve   # L3 smoke test zonder HITL prompt
```

`start.sh` maakt bij de eerste run een `.venv/` aan en installeert `requirements.txt`.

### Vereisten

| Tool / var | Waarom |
|---|---|
| Python 3.10+ | venv + typing-syntax (`list[...] \| None`) |
| `OPENAI_API_KEY` | OpenAI-calls (key via [platform.openai.com](https://platform.openai.com/api-keys)) |
| `OPENAI_MODEL` (optioneel) | model-override, default `gpt-5.4-mini` |

## Waarom niet op Vercel

L3 gebruikt een revisie-loop met `interrupt()` + checkpointing (HITL via de terminal).
Dat is een interactief, langlopend proces dat niet in een serverless function past. Wil
je later een gedeelde demo, wrap dan L2 (of een auto-approve L3) in een UI en host als
`runtime: python-server` (Streamlit/Gradio op HF Spaces/Railway) — dan hoort er wél een
`url:` in het manifest.

## Checklist

- [x] `deploy: false`, geen `url:` in het manifest
- [x] Geen secrets in de repo (`.env` staat in `.gitignore`; alleen `.env.example`)
- [x] Run-instructie hierboven ingevuld
