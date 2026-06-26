# HOSTING — PydanticAI (python-serverless)

`runtime: python-serverless`, `deploy: true` — een FastAPI-app die de pipeline draait
en als serverless function op Vercel staat (project `cookbook-pydanticai`), achter de
gedeelde wachtwoord-gate. De CLI (`start.sh`) werkt los voor lokaal experimenteren.

## Structuur

```
src/
  api/
    index.py        # FastAPI-app (ASGI `app`); GET / serveert de UI, POST /run draait de pipeline
    _ui.py          # de web-UI als HTML-string
  common.py         # casus + PydanticAI-agents + steps (gedeeld door CLI én API)
  l1_writer.py / l2_chain.py / l3_orchestrator.py   # generate() + CLI-runner per niveau
  inputs.py
  middleware.ts     # SITE_PASSWORD-gate
  vercel.json       # rewrite: alle routes → /api/index
  requirements.txt
  start.sh
```

## Web-UI lokaal draaien

```bash
cd src
cp .env.example .env                 # vul OPENAI_API_KEY in
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt uvicorn
uvicorn api.index:app --reload       # http://localhost:8000
```

CLI los: `./start.sh l3 -- --auto-approve`.

## L3 in de browser = auto-approve

L1/L2 zijn single-shot. **L3 draait in de web-UI in `auto-approve`**: de revisie-loop +
guard werken, maar de échte HITL-pauze niet — serverless functions zijn stateless. Voor de
interactieve HITL: gebruik de CLI (`./start.sh l3`). Anders dan LangGraph gebruikt
PydanticAI hier géén graph-runtime/checkpointing; de loop is plain Python in-memory.

## Env vars

| Variabele | Verplicht | Hoe |
|---|---|---|
| `OPENAI_API_KEY` | **Ja** | Na de eerste deploy zelf zetten: Vercel-project → Settings → Environment Variables → redeploy. Zonder key geeft `/run` een nette 503. |
| `OPENAI_MODEL` | Nee | Model-override, default `gpt-5.4-mini`. |
| `SITE_PASSWORD` | — | Wordt automatisch door de provisioning-workflow gezet (de gate). |
| `LOGFIRE_TOKEN` | Nee | Deep-tracing via [Pydantic Logfire](https://logfire.pydantic.dev) (PydanticAI-native). **Voeg dan ook `logfire` toe aan `requirements.txt`.** Status zichtbaar in `/api/health` + de metabar. |

## Eigen input & observability

- **Eigen input**: de UI vult de vaste casus voor als default (`GET /api/defaults`), maar
  briefing/lengte/toon/`must_*`/structuur zijn vrij overschrijfbaar. Voor een eerlijke
  vergelijking laat je de standaard-casus staan.
- **Observability (in-app)**: per run de LLM-calls, latency en token-gebruik (uit
  `result.usage()`), met totalen + per-step tabel. Werkt zonder extra account.
- **Observability (Logfire)**: zet `LOGFIRE_TOKEN` + voeg `logfire` toe → elke agent-run
  wordt getraced met volledige waterfall.

## Live zetten (automatisch)

`deploy: true` staat al in `cookbook.yaml`. Bij merge naar `main` maakt de
provisioning-workflow `cookbook-pydanticai` aan (root `cookbooks/pydanticai/src`) en deployt.
Daarna:

1. Zet `OPENAI_API_KEY` in de Vercel project settings en redeploy.
2. Test op `https://cookbook-pydanticai.vercel.app` (de gate vraagt het teamwachtwoord).
3. Zet die URL als `url:` in `cookbook.yaml` (vervolg-PR) voor de "Open"-knop.

## Checklist

- [ ] `uvicorn api.index:app` werkt lokaal (UI laadt, een run lukt)
- [x] `requirements.txt` compleet
- [x] `middleware.ts` aanwezig (zonder dit staat de deploy open op internet)
- [x] Geen secrets in de repo (`.env` gitignored; key via Vercel settings)
- [ ] Dependencies passen binnen de ~250MB bundle-limiet
- [ ] Na eerste deploy: `OPENAI_API_KEY` gezet en `url:` in het manifest
