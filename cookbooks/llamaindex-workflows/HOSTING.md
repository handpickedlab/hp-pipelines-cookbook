# HOSTING — LlamaIndex Workflows (python-serverless)

`runtime: python-serverless`, `deploy: true` — een FastAPI-app die de pipeline draait en
als serverless function op Vercel staat (project `cookbook-llamaindex-workflows`), achter
de gedeelde wachtwoord-gate. De CLI (`start.sh`) werkt los voor lokaal experimenteren.

## ⚠️ Bundle-grootte

LlamaIndex is de zwaarste van de framework-cookbooks: `llama-index-core` trekt numpy,
sqlalchemy, networkx, PIL en nltk mee (~190MB aan deps). Dat zit **onder** de ~250MB
serverless-limiet, maar met de minste marge. Mocht een toekomstige dep-bump er overheen
gaan en de deploy falen, dan is de fallback: `deploy: false` (alleen CLI) of `runtime:
python-server` (extern hosten).

## Structuur

```
src/
  api/
    index.py        # FastAPI-app (ASGI `app`); GET / serveert de UI, POST /run draait de pipeline
    _ui.py          # de web-UI als HTML-string
  common.py         # casus + LlamaIndex LLM-laag (token-counting) + de pipeline-steps
  l1_writer.py / l2_chain.py / l3_orchestrator.py   # Workflow + generate() + CLI-runner per niveau
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

## L3, HITL en checkpointing

L1/L2 zijn single-shot. L3 is een echte Workflow met een revisie-loop (events lopen terug)
en de ingebouwde **`InputRequiredEvent`/`HumanResponseEvent`** voor human-in-the-loop. In de
web-UI draait L3 in **auto-approve** (de runner beantwoordt de InputRequiredEvent
automatisch); de interactieve HITL werkt via de CLI (`./start.sh l3`). LlamaIndex heeft ook
een `WorkflowCheckpointer` voor resume — niet bedraad hier, wél een sterk punt t.o.v.
PydanticAI (dat HITL handmatig wiret).

## Env vars

| Variabele | Verplicht | Hoe |
|---|---|---|
| `OPENAI_API_KEY` | **Ja** | Na de eerste deploy zelf zetten: Vercel-project → Settings → Environment Variables → redeploy. Zonder key geeft `/run` een nette 503. |
| `OPENAI_MODEL` | Nee | Model-override, default `gpt-5.4-mini`. |
| `SITE_PASSWORD` | — | Wordt automatisch door de provisioning-workflow gezet (de gate). |

## Observability

- **In-app**: per run de LLM-calls, latency en token-gebruik (via LlamaIndex
  `TokenCountingHandler`), met totalen + per-step tabel. Werkt zonder extra account.
- **Deep-tracing**: LlamaIndex instrumenteert via OpenTelemetry — koppel bv. Arize Phoenix
  of Langfuse als je volledige call-traces wilt.

## Live zetten (automatisch)

`deploy: true` staat al in `cookbook.yaml`. Bij merge naar `main` maakt de
provisioning-workflow `cookbook-llamaindex-workflows` aan (root `cookbooks/llamaindex-workflows/src`)
en deployt. Daarna:

1. Zet `OPENAI_API_KEY` in de Vercel project settings en redeploy.
2. Test op `https://cookbook-llamaindex-workflows.vercel.app` (de gate vraagt het teamwachtwoord).
3. Zet die URL als `url:` in `cookbook.yaml` (vervolg-PR) voor de "Open"-knop.

## Checklist

- [ ] `uvicorn api.index:app` werkt lokaal (UI laadt, een run lukt)
- [x] `requirements.txt` compleet
- [x] `middleware.ts` aanwezig (zonder dit staat de deploy open op internet)
- [x] Geen secrets in de repo (`.env` gitignored; key via Vercel settings)
- [ ] Bundle binnen de ~250MB limiet (zie waarschuwing boven)
- [ ] Na eerste deploy: `OPENAI_API_KEY` gezet en `url:` in het manifest
