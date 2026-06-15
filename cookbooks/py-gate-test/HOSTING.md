# HOSTING — python-serverless (FastAPI/Flask op Vercel)

Dit cookbook is een Python-API die als serverless functions op Vercel draait, in een eigen Vercel-project op het Handpicked-team.

## Beperkingen (lees dit eerst)

- Geen long-running processes of background workers; requests zijn kortlevend.
- Bundle-limiet ~250MB — zware ML-dependencies (torch e.d.) passen niet. Heb je die nodig, kies dan `runtime: python-server` en host extern.
- Cold starts zijn normaal.

## Werkend FastAPI-voorbeeld

Vercel herkent Python-functions in een `api/`-map. Deze structuur deployt zonder verdere configuratie van build commands:

```
cookbooks/<slug>/src/
  api/
    index.py          # de hele FastAPI-app
  requirements.txt
  vercel.json
```

`api/index.py` — Vercel zoekt naar een ASGI-app genaamd `app`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/api/hello")
def hello(name: str = "wereld"):
    return {"message": f"Hallo, {name}"}
```

`requirements.txt`:

```
fastapi==0.115.*
```

`vercel.json` — stuurt alle routes naar de FastAPI-app, zodat FastAPI zelf de routing doet:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/api/index" }]
}
```

## Lokaal draaien

```bash
cd src
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt uvicorn
uvicorn api.index:app --reload      # http://localhost:8000
```

(`uvicorn` is alleen lokaal nodig; op Vercel draait de ASGI-app in hun eigen runtime.)

## Wachtwoordbeveiliging

Kopieer `templates/middleware.ts` naar je `src/` — Routing Middleware draait vóór je Python-functions, dus dit beschermt ook je API-endpoints (env var `SITE_PASSWORD`, wordt automatisch gezet bij provisioning). Zonder dit bestand staat je deploy **open op internet**.

## Live zetten (automatisch)

Zet `deploy: true` in `cookbook.yaml` en merge naar `main`. De provisioning-workflow maakt dan automatisch het Vercel-project aan (`cookbook-<slug>`, root directory `cookbooks/<slug>/src`, ignored-build-step ingesteld) en deployt meteen. Daarna:

1. Test een endpoint op `https://cookbook-<slug>.vercel.app`.
2. Env vars nodig (API-keys e.d.)? Vercel-dashboard → project → Settings → Environment Variables (namen volgens `.env.example` in de repo-root), daarna redeployen.
3. Zet de URL als `url:` in `cookbook.yaml` (vervolg-PR) voor de "Open"-knop in de catalogus.

Handmatig aanmaken kan ook nog (dashboard → Add New → Project → zelfde repo, root directory op jouw `src/`, framework preset **Other**), bv. als de workflow faalt.

## Checklist

- [ ] `uvicorn api.index:app` werkt lokaal
- [ ] `requirements.txt` compleet en gepind
- [ ] Geen secrets in de repo — env vars via Vercel project settings
- [ ] Dependencies passen binnen de bundle-limiet
- [ ] Na eerste deploy: `url:` en `deploy: true` in het manifest gezet
