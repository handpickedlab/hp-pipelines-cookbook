# Handpicked Cookbooks

Experiment-sandbox voor het Handpicked-team: één monorepo met onafhankelijk deploybare cookbooks, plus een centrale index-site (catalogus) op Vercel.

**Nieuw hier? Volg [TUTORIAL.md](TUTORIAL.md)** — van clone tot live cookbook in ~15 minuten. Live catalogus: [hp-cookbooks-index.vercel.app](https://hp-cookbooks-index.vercel.app).

Een **cookbook** is een zelfstandig experiment: een web-app, een workflow (bv. n8n-export), of een notebook. Elk cookbook leeft in zijn eigen map onder `cookbooks/`, beschrijft zichzelf in een `cookbook.yaml`, en legt in een `HOSTING.md` uit hoe en waar het draait.

## Structuur

```
cookbooks/
  <slug>/
    cookbook.yaml      # manifest: wat is dit, wie owned het, hoe wordt het gehost
    HOSTING.md         # hoe en waar dit cookbook draait (template per runtime)
    src/               # de eigenlijke code/bestanden
index/                 # Next.js catalogus-site die alle manifests rendert
templates/             # cookbook.yaml-template + HOSTING.md-recepten per runtime
.github/workflows/     # manifest-validatie in CI
```

## Een cookbook toevoegen

1. Kopieer `templates/cookbook.yaml` naar `cookbooks/<jouw-slug>/cookbook.yaml` en vul hem in. De slug is kebab-case en moet gelijk zijn aan de mapnaam. Alle velden, toegestane waarden en de consequenties van fout invullen: [MANIFEST.md](MANIFEST.md).
2. Kies het `runtime` dat past en kopieer het bijbehorende recept uit `templates/hosting/` naar `cookbooks/<jouw-slug>/HOSTING.md`. Volg het recept.
3. Zet je code in `src/`.
4. Open een PR. CI valideert je manifest; de PR-template loopt de checklist met je door.

### Runtimes

| `runtime` | Wat | Waar gehost |
|---|---|---|
| `node` | Next.js/static/Node web-app | Eigen Vercel-project op het Handpicked-team |
| `python-serverless` | FastAPI/Flask als serverless functions | Eigen Vercel-project (let op: geen long-running processes, ~250MB bundle-limiet) |
| `python-server` | Streamlit/Gradio/Dash — persistent process | Extern (HF Spaces, Railway, Fly.io); URL in het manifest |
| `notebook` | Jupyter/marimo | Statisch (nbconvert-HTML) of marimo-WASM op Vercel |
| `none` | Workflow-exports (n8n-JSON), docs, datasets | Niet gedeployd; de index linkt naar de bestanden |

## Index-site

```bash
cd index
npm install
npm run dev        # http://localhost:3000
```

De site leest bij build alle `cookbooks/*/cookbook.yaml` en rendert de catalogus. Op Vercel: project-root op `index/`, met een ignored-build-step zodat alleen wijzigingen in `index/` of manifests een rebuild triggeren (zie `index/README.md`).

## Manifest valideren (lokaal)

```bash
node index/scripts/validate.mjs
```

CI draait dezelfde check op elke PR.

## Toegang

De catalogus en de gedeployde cookbooks zitten achter een gedeelde **wachtwoord-gate**: een eigen HTML-loginpagina (geen kale browser-popup) die de toegang in een cookie onthoudt (HttpOnly/Secure/SameSite, 30 dagen). Vraag het teamwachtwoord aan Niek.

Technisch: `templates/middleware.ts` is Vercel Routing Middleware en checkt de env var `SITE_PASSWORD`, die de provisioning-workflow automatisch op nieuwe projecten zet. Cookbooks kopiëren dit bestand naar hun `src/` — **zonder dat bestand staat een deploy open op internet**. Lokaal (zonder de env var) is alles gewoon open.

### Waar de gate wél en niet werkt

Routing Middleware draait op de Vercel-laag vóór je app, dus de gate beschermt alles wat **op Vercel** gehost wordt — ongeacht de runtime daaronder. Verkeer dat extern draait, raakt de gate nooit.

| Runtime | Gate werkt? | Toelichting |
|---|---|---|
| `node` (Next.js, Vite, static) | ✅ Ja | Geverifieerd op de catalogus en op een static cookbook. |
| `python-serverless` (FastAPI/Flask) | ✅ Ja | Geverifieerd: middleware draait vóór de Python-functions; niet-ingelogd → gate, ingelogd → API. |
| `python-server` (Streamlit/Gradio/Dash) | ❌ Nee | Extern gehost (HF Spaces/Railway/Fly). Vercel-middleware draait daar niet — regel auth op die host zelf. |
| `notebook` | ⚠️ Afhankelijk | Statisch op Vercel → ✅. Extern (bv. marimo elders gehost) → ❌, net als `python-server`. |
| `none` | — | Wordt niet gedeployd; niets om af te schermen. |

Praktisch: een *ingelogde* gebruiker (geldige cookie) gaat gewoon door naar je app, dus de gate botst niet met je eigen routes of POST-endpoints — alleen niet-ingelogde requests worden onderschept. Host je extern (`python-server`), zet daar dan je eigen wachtwoord/SSO; de `SITE_PASSWORD`-gate dekt dat niet.

## Deploy-provisioning (automatisch)

Zet `deploy: true` in je manifest en merge naar `main` — de provisioning-workflow (`.github/workflows/provision.yml`) maakt dan automatisch een Vercel-project aan (`cookbook-<slug>`, root directory op jouw `src/`) en triggert de eerste deploy. Je app komt live op `https://cookbook-<slug>.vercel.app`; zet die URL daarna als `url:` in je manifest. Geldt voor runtime `node` en `python-serverless`; extern gehoste runtimes worden overgeslagen. Vereist het repo-secret `VERCEL_TOKEN`.

---

*De eerdere inhoud van deze repo (de framework-vergelijking n8n/Mastra/LangGraph/Dify/Pydantic AI/AgentField) staat in de git-history vóór de cookbook-toolkit-omslag.*
