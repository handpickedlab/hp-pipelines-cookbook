# HOSTING — node (web-app op Vercel)

Dit cookbook is een web-app (Next.js, Vite, of puur statisch) en krijgt een eigen Vercel-project op het Handpicked-team.

## Lokaal draaien

```bash
cd src
npm install
npm run dev
```

*(Pas aan naar jouw stack; dit blok moet kloppen voor wie het cookbook checkt.)*

## Live zetten (automatisch)

Zet `deploy: true` in `cookbook.yaml` en merge naar `main`. De provisioning-workflow maakt dan automatisch het Vercel-project aan (`cookbook-<slug>`, root directory `cookbooks/<slug>/src`, ignored-build-step ingesteld) en deployt meteen. Daarna:

1. Check `https://cookbook-<slug>.vercel.app`.
2. Env vars nodig? Vercel-dashboard → project → Settings → Environment Variables (namen volgens `.env.example` in de repo-root), daarna redeployen.
3. Zet de URL als `url:` in `cookbook.yaml` (vervolg-PR) voor de "Open"-knop in de catalogus.

Handmatig aanmaken kan ook nog (dashboard → Add New → Project → zelfde repo, root directory op jouw `src/`), bv. als de workflow faalt.

## Checklist

- [ ] `npm run build` slaagt lokaal
- [ ] Geen secrets in de repo — env vars via Vercel project settings
- [ ] `url:` in het manifest gevuld na eerste deploy
