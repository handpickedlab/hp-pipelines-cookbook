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

## Vercel-project aanmaken (eenmalig, na merge)

Dit doe je één keer; daarna deployt elke push naar `main` automatisch.

1. Vercel-dashboard → Handpicked-team → **Add New… → Project** → kies deze repo ("Add another project from the same repo").
2. **Root Directory**: `cookbooks/<slug>/src`
3. Framework preset: **Other** (er is geen frontend-framework; de `api/`-map wordt automatisch herkend).
4. Env vars nodig (API-keys e.d.)? Settings → Environment Variables. Namen volgens `.env.example` in de repo-root.
5. **Ignored Build Step** (Settings → Git), zodat alleen wijzigingen aan dit cookbook een build triggeren:
   ```bash
   git diff HEAD^ HEAD --quiet -- ../
   ```
6. Deploy, test een endpoint, en zet daarna in `cookbook.yaml`: `deploy: true` en `url: https://...`.

## Checklist

- [ ] `uvicorn api.index:app` werkt lokaal
- [ ] `requirements.txt` compleet en gepind
- [ ] Geen secrets in de repo — env vars via Vercel project settings
- [ ] Dependencies passen binnen de bundle-limiet
- [ ] Na eerste deploy: `url:` en `deploy: true` in het manifest gezet
