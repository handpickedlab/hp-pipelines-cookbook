# HOSTING — LangGraph (python-serverless)

`runtime: python-serverless`, `deploy: true` — een FastAPI-app die de pipeline draait
en als serverless function op Vercel staat, in een eigen project (`cookbook-langgraph`),
achter de gedeelde wachtwoord-gate. Daarnaast blijft de CLI (`start.sh`) werken voor
lokaal experimenteren.

## Structuur

```
src/
  api/
    index.py        # FastAPI-app (ASGI `app`); GET / serveert de UI, POST /run draait de pipeline
    _ui.py          # de web-UI als HTML-string (.py i.v.m. bundling)
  common.py …       # de pipeline (ongewijzigd, gedeeld door CLI én API)
  l1_writer.py / l2_chain.py / l3_orchestrator.py
  inputs.py
  middleware.ts     # SITE_PASSWORD-gate (Routing Middleware, vóór de Python-functions)
  vercel.json       # rewrite: alle routes → /api/index
  requirements.txt
  start.sh          # CLI-runner (los van de web-UI)
```

## Web-UI lokaal draaien

```bash
cd src
cp .env.example .env                 # vul OPENAI_API_KEY in
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt uvicorn
uvicorn api.index:app --reload       # http://localhost:8000
```

(`uvicorn` is alleen lokaal nodig; op Vercel draait de ASGI-app in hun runtime.)
De CLI blijft los werken: `./start.sh l3 -- --auto-approve`.

## L3 in de browser = auto-approve

L1/L2 zijn single-shot en passen perfect in serverless. **L3 draait in de web-UI in
`auto-approve`-modus**: de revisie-loop + guard + checkpointing werken, maar de échte
HITL-pauze (mens keurt goed/af) niet — serverless functions zijn stateless en houden de
`interrupt()`-checkpoint niet vast tussen requests. Voor de interactieve HITL: gebruik de
CLI (`./start.sh l3`). L3 kan tot 9 LLM-calls doen; met een reasoning-model (default
`gpt-5.4-mini`) kan dat richting de 300s-functietimeout lopen.

## Env vars

| Variabele | Verplicht | Hoe |
|---|---|---|
| `OPENAI_API_KEY` | **Ja** | Na de eerste deploy zelf zetten: Vercel-project → Settings → Environment Variables → redeploy. Zonder key geeft `/run` een nette 503. |
| `OPENAI_MODEL` | Nee | Model-override, default `gpt-5.4-mini`. |
| `SITE_PASSWORD` | — | Wordt automatisch door de provisioning-workflow gezet (de gate). |

## Live zetten (automatisch)

`deploy: true` staat al in `cookbook.yaml`. Bij merge naar `main` maakt de
provisioning-workflow het project `cookbook-langgraph` aan (root `cookbooks/langgraph/src`)
en deployt. Daarna:

1. Zet `OPENAI_API_KEY` in de Vercel project settings en redeploy.
2. Test op `https://cookbook-langgraph.vercel.app` (de gate vraagt het teamwachtwoord).
3. Zet die URL als `url:` in `cookbook.yaml` (vervolg-PR) voor de "Open"-knop in de catalogus.

## Checklist

- [ ] `uvicorn api.index:app` werkt lokaal (UI laadt, een run lukt)
- [x] `requirements.txt` compleet en gepind
- [x] `middleware.ts` aanwezig (zonder dit staat de deploy open op internet)
- [x] Geen secrets in de repo (`.env` gitignored; key via Vercel settings)
- [ ] Dependencies passen binnen de ~250MB bundle-limiet
- [ ] Na eerste deploy: `OPENAI_API_KEY` gezet en `url:` in het manifest
