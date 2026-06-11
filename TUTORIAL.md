# Tutorial: je eerste cookbook, van nul tot live

Deze tutorial neemt je in ~15 minuten mee van een verse clone naar een eigen cookbook in de catalogus op [hp-cookbooks-index.vercel.app](https://hp-cookbooks-index.vercel.app). Geen voorkennis van de repo nodig.

## Hoe het werkt, in één minuut

- Deze repo is een verzameling losse experimenten (**cookbooks**), elk in een eigen map onder `cookbooks/`. Cookbooks delen géén code of toolchain — een cookbook kan een Next.js-app zijn, een FastAPI'tje, een n8n-export of een notebook.
- Elk cookbook beschrijft zichzelf in een **`cookbook.yaml`** (manifest). De catalogus-site in `index/` leest bij build alle manifests en rendert daar de kaarten van. Jouw cookbook in de catalogus krijgen = een geldig manifest mergen naar `main`. Meer is het niet.
- Elk cookbook heeft een **`HOSTING.md`**: hoe draait dit lokaal, en waar draait het live. Web-apps krijgen een **eigen Vercel-project** (de catalogus en de cookbooks deployen onafhankelijk van elkaar); dingen die niet op Vercel passen draaien extern en worden alleen gelinkt.
- CI valideert elk manifest op elke PR. Een kapot manifest komt `main` niet op.

## Stap 0 — Vereisten

- Node 22+ (voor de index-site en de validator)
- Toegang tot de repo: `github.com/handpickedlab/hp-pipelines-cookbook`
- Alleen nodig als je gaat deployen: toegang tot het `handpicked-lab` Vercel-team

## Stap 1 — Clone en verken

```bash
git clone git@github.com:handpickedlab/hp-pipelines-cookbook.git
cd hp-pipelines-cookbook
```

De plekken die ertoe doen:

| Pad | Wat |
|---|---|
| `cookbooks/` | Alle experimenten. Kijk in `cookbooks/hello-cookbook/` voor het minimale voorbeeld. |
| `templates/` | Startpunten: het manifest-template en per runtime een hosting-recept. |
| `index/` | De catalogus-site (Next.js). Hoef je normaal niet aan te raken. |

## Stap 2 — Draai de catalogus lokaal

```bash
cd index
npm install
npm run dev
```

Open http://localhost:3000 — je ziet de catalogus met de bestaande cookbooks. Laat dit draaien; straks verschijnt jouw cookbook er live tussen (na herstart van de dev-server, manifests worden bij build gelezen).

## Stap 3 — Maak je cookbook-map

Werk op een branch:

```bash
git checkout -b cookbook/mijn-experiment
mkdir -p cookbooks/mijn-experiment/src
cp templates/cookbook.yaml cookbooks/mijn-experiment/cookbook.yaml
```

Vul `cookbook.yaml` in. De twee velden waar je even over na moet denken:

- **`type`** — wat is het? `app` (iets met een UI), `workflow` (bv. n8n-export), of `notebook`.
- **`runtime`** — hoe draait het? Dit bepaalt je hosting-route:

| Jouw situatie | `runtime` |
|---|---|
| Next.js / Vite / statische site | `node` |
| FastAPI of Flask zonder zware dependencies | `python-serverless` |
| Streamlit / Gradio / Dash, of zware ML-deps | `python-server` (extern gehost, URL verplicht) |
| Jupyter of marimo notebook | `notebook` |
| Alleen bestanden (n8n-JSON, prompts, dataset) | `none` |

Let op: `slug` moet **exact** de mapnaam zijn (`mijn-experiment`), anders faalt de validatie. De volledige veldreferentie — alle toegestane waarden en wat er misgaat bij fout invullen — staat in [MANIFEST.md](MANIFEST.md).

## Stap 4 — Kopieer het hosting-recept

```bash
cp templates/hosting/<jouw-runtime>.md cookbooks/mijn-experiment/HOSTING.md
```

Pas het aan: het "Lokaal draaien"-blok moet kloppen voor jouw code. Dit bestand is wat een collega over drie maanden leest om jouw experiment werkend te krijgen — schrijf het voor die persoon.

## Stap 5 — Bouw je experiment

Zet je code in `cookbooks/mijn-experiment/src/`. Alles mag, drie regels:

1. **Geen secrets in de repo.** API-keys gaan via env vars (Vercel project settings) of moeten door de gebruiker zelf worden aangemaakt (documenteer de namen in `HOSTING.md`).
2. **Blijf in je eigen map.** Cookbooks importeren niks van elkaar en niks uit `index/`.
3. **Ga je deployen? Kopieer `templates/middleware.ts` naar je `src/`.** Dat zet je cookbook achter het gedeelde teamwachtwoord (basic auth); zonder dit bestand staat je deploy open op internet. Het wachtwoord zelf wordt bij provisioning automatisch als env var gezet — vraag het aan Niek.

## Stap 6 — Valideer

```bash
node index/scripts/validate.mjs
```

Dit is exact dezelfde check als CI straks draait. Veelvoorkomende fouten: slug ≠ mapnaam, `HOSTING.md` vergeten, `runtime: python-server` zonder `url:`.

## Stap 7 — Open een PR

```bash
git add cookbooks/mijn-experiment
git commit -m "Add mijn-experiment cookbook"
git push -u origin cookbook/mijn-experiment
```

De PR-template bevat de checklist; CI valideert je manifest en bouwt de catalogus. Na merge naar `main` deployt de catalogus automatisch en staat je cookbook op [hp-cookbooks-index.vercel.app](https://hp-cookbooks-index.vercel.app).

## Stap 8 — (Alleen voor deploybare apps) Zet hem live

Heeft je cookbook `runtime: node` of `python-serverless` en wil je hem live? Zet dan gewoon **`deploy: true`** in je `cookbook.yaml` vóór je merget. Bij de merge naar `main` maakt de provisioning-workflow automatisch een Vercel-project voor je aan (`cookbook-mijn-experiment`, root directory op jouw `src/`) en deployt hem meteen. Je app staat daarna op:

```
https://cookbook-mijn-experiment.vercel.app
```

Zet die URL als `url:` in je manifest (kleine vervolg-PR) en de catalogus toont een "Open"-knop. Env vars (API-keys) zet je daarna in het Vercel-dashboard bij het nieuwe project: Settings → Environment Variables.

Voor `python-server` (Streamlit e.d.): hier doet de workflow niets — host op HF Spaces of Railway volgens je `HOSTING.md`, en zet alleen de `url:` in het manifest.

## Veelgestelde vragen

**Wat gaat automatisch en wat is handmatig?**
Mergen naar `main` = je cookbook staat automatisch in de catalogus. Met `deploy: true` wordt bij diezelfde merge ook automatisch een Vercel-project aangemaakt en je app live gezet (stap 8). Daarna deployt elke push die jouw cookbook raakt automatisch. Handmatig blijft alleen: env vars instellen in het dashboard, en de `url:` in je manifest zetten.

**Moet mijn experiment af zijn voordat het erin mag?**
Nee — dit is een sandbox. Een half experiment met een eerlijke beschrijving is prima; daar is het `tags`-veld en de description voor.

**Kan ik een bestaand project erin hangen dat al ergens anders gehost is?**
Ja: `runtime` naar wat het is, `url:` naar waar het draait, code (of een verwijzing) in `src/`.

**Ik wil een veld toevoegen aan cookbook.yaml.**
Kan, maar het schema leeft op vier plekken: `index/scripts/validate.mjs`, `templates/cookbook.yaml`, `index/lib/cookbooks.ts` en de docs. Eén PR die ze alle vier bijwerkt.

**Wie maakt het Vercel-project aan?**
De CI — automatisch bij merge, zodra `deploy: true` in je manifest staat. Zie stap 8.
