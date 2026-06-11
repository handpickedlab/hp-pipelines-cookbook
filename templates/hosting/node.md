# HOSTING — node (web-app op Vercel)

Dit cookbook is een web-app (Next.js, Vite, of puur statisch) en krijgt een eigen Vercel-project op het Handpicked-team.

## Lokaal draaien

```bash
cd src
npm install
npm run dev
```

*(Pas aan naar jouw stack; dit blok moet kloppen voor wie het cookbook checkt.)*

## Vercel-project aanmaken (eenmalig, na merge)

1. Vercel-dashboard → Handpicked-team → **Add New… → Project** → importeer deze repo (staat er al — kies "Add another project from the same repo").
2. **Root Directory**: `cookbooks/<slug>/src`
3. Framework preset wordt meestal automatisch herkend; controleer build command en output.
4. **Ignored Build Step** (Settings → Git), zodat alleen wijzigingen in dit cookbook een build triggeren:
   ```bash
   git diff HEAD^ HEAD --quiet -- ../
   ```
5. Na de eerste deploy: zet de productie-URL in `cookbook.yaml` onder `url:` en zet `deploy: true`.

## Checklist

- [ ] `npm run build` slaagt lokaal
- [ ] Geen secrets in de repo — env vars via Vercel project settings
- [ ] `url:` in het manifest gevuld na eerste deploy
