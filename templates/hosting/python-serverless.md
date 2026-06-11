# HOSTING — python-serverless (FastAPI/Flask op Vercel)

Dit cookbook is een Python-API die als serverless functions op Vercel draait, in een eigen Vercel-project op het Handpicked-team.

## Beperkingen (lees dit eerst)

- Geen long-running processes of background workers; requests zijn kortlevend.
- Bundle-limiet ~250MB — zware ML-dependencies (torch e.d.) passen niet. Heb je die nodig, kies dan `python-server` en host extern.
- Cold starts zijn normaal.

## Lokaal draaien

```bash
cd src
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload     # of jouw equivalent
```

## Vercel-project aanmaken (eenmalig, na merge)

1. Vercel-dashboard → Handpicked-team → **Add New… → Project** → zelfde repo, nieuw project.
2. **Root Directory**: `cookbooks/<slug>/src`
3. Zorg dat je entrypoint Vercels Python-conventie volgt (bv. `api/index.py` die de FastAPI-app exporteert) of een `vercel.json` met rewrites bevat.
4. **Ignored Build Step**: `git diff HEAD^ HEAD --quiet -- ../`
5. Na de eerste deploy: `url:` invullen in `cookbook.yaml` en `deploy: true` zetten.

## Checklist

- [ ] `requirements.txt` compleet en gepind
- [ ] Geen secrets in de repo — env vars via Vercel project settings
- [ ] Dependencies passen binnen de bundle-limiet
