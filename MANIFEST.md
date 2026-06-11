# cookbook.yaml — veldreferentie

Wat elk veld doet, welke waarden mogen, en wat er gebeurt als je het verkeerd invult.

**Het belangrijkste om te snappen:** het manifest deployt niets. Het stuurt twee dingen aan: wat de catalogus toont, en welke regels CI afdwingt. Een fout manifest kan dus nooit een deployment slopen — de worst case is een PR die niet door CI komt, of een catalogus die iets misleidends toont.

## Twee soorten fouten

| Soort | Wat gebeurt er | Voorbeelden |
|---|---|---|
| **Ongeldig** — de validator vangt het | CI faalt, je PR kan niet gemerged worden. Je ziet per fout een regel in de Actions-log. Lokaal vooraf checken: `node index/scripts/validate.mjs` | slug ≠ mapnaam, onbekende `runtime`, ontbrekende `description`, `python-server` zonder `url` |
| **Geldig maar onwaar** — glipt door CI heen | De catalogus toont verkeerde informatie. Niets crasht, maar collega's worden op het verkeerde been gezet | dode `url:` (kapotte "Open"-knop), verkeerde `runtime` (collega volgt het verkeerde hosting-recept), `owner` die het team al verlaten heeft |

## De velden

### `slug` — verplicht

Kebab-case (`a-z`, `0-9`, koppeltekens), **exact gelijk aan de mapnaam**.

- *Gebruikt voor*: de "Broncode"-link in de catalogus wijst naar `cookbooks/<slug>/`.
- *Fout ingevuld*: mismatch met mapnaam → CI blokkeert. Geen stille fouten mogelijk.

### `name` — verplicht

Vrije weergavenaam, mag spaties en hoofdletters bevatten.

- *Gebruikt voor*: de kaarttitel en de (alfabetische) sortering in de catalogus.
- *Fout ingevuld*: alleen cosmetisch.

### `description` — verplicht

1–2 zinnen. Gebruik YAML's `>` voor meerregelig.

- *Gebruikt voor*: de tekst op de kaart. Dit is hoe collega's beslissen of ze klikken.
- *Fout ingevuld*: alleen cosmetisch, maar een vage description maakt je cookbook onvindbaar in een groeiende catalogus.

### `type` — verplicht — `app` | `workflow` | `notebook`

Wát het is, los van hoe het draait.

- *Gebruikt voor*: het gekleurde badge op de kaart (blauw/groen/oranje).
- *Fout ingevuld*: waarde buiten de enum → CI blokkeert. Verkeerde maar geldige keuze → alleen een verkeerd badge.

### `runtime` — verplicht — `node` | `python-serverless` | `python-server` | `notebook` | `none`

Hóe het draait. **Dit is het veld met de meeste gevolgen**, want het bepaalt welk hosting-recept geldt en welke extra CI-regels gelden:

| Waarde | Hosting-route | Extra CI-regel |
|---|---|---|
| `node` | Eigen Vercel-project | — |
| `python-serverless` | Eigen Vercel-project (Python functions) | — |
| `python-server` | Extern (HF Spaces, Railway, …) | `url:` is **verplicht** |
| `notebook` | Statisch gerenderd | — |
| `none` | Niet gedeployd | `deploy: true` is **verboden** |

- *Fout ingevuld (ongeldig)*: CI blokkeert.
- *Fout ingevuld (verkeerde keuze)*: niemand merkt het tot iemand jouw `HOSTING.md` volgt en vastloopt — bv. `node` gekozen voor een Streamlit-app die helemaal niet op Vercel kán. Twijfel je? Zie de keuzetabel in [TUTORIAL.md](TUTORIAL.md) stap 3.

### `stack` — verplicht (mag leeg: `[]`)

Vrije lijst met technologieën, bv. `[fastapi]`, `[nextjs, tailwind]`, `[n8n]`.

- *Gebruikt voor*: de "Stack"-regel op de kaart.
- *Fout ingevuld*: geen lijst-syntax → CI blokkeert. Inhoud is vrij en alleen informatief.

### `owner` — verplicht

Wie je kunt aanspreken over dit cookbook.

- *Gebruikt voor*: de "Owner"-regel op de kaart.
- *Fout ingevuld*: CI checkt alleen dat het niet leeg is. Een verkeerde naam betekent dat vragen bij de verkeerde persoon landen — houd dit bij als experimenten van eigenaar wisselen.

### `deploy` — verplicht — `true` | `false`

Of dit cookbook een eigen Vercel-project heeft (of hoort te krijgen).

- *Gebruikt voor*: administratie + de geplande provisioning-workflow gaat hierop selecteren.
- *Fout ingevuld*: geen boolean → CI blokkeert. `true` zonder dat het project bestaat → niets breekt vandaag, maar zodra provisioning live is wordt dit veld sturend, dus houd het waar.

### `url` — optioneel (verplicht bij `runtime: python-server`)

Moet met `http(s)://` beginnen.

- *Gebruikt voor*: de "Open ↗"-knop in de catalogus.
- *Fout ingevuld*: geen http(s) → CI blokkeert. Dode link → kapotte knop; CI checkt **niet** of de URL bereikbaar is.

### `tags` — optioneel (default `[]`)

Vrije labels, bv. `[llm, orchestration]`.

- *Gebruikt voor*: de tag-chips op de kaart; bedoeld voor filteren zodra de catalogus dat krijgt.
- *Fout ingevuld*: geen lijst → CI blokkeert. Inhoud is vrij.

### Onbekende velden

Elk veld dat hierboven niet staat → CI blokkeert. Dit is bewust: het schema leeft op vier plekken (`index/scripts/validate.mjs`, `templates/cookbook.yaml`, `index/lib/cookbooks.ts`, deze docs) en een nieuw veld hoort op alle vier tegelijk te landen, in één PR.

## Compleet voorbeeld

```yaml
slug: invoice-classifier          # = mapnaam, kebab-case
name: Invoice Classifier
description: >
  FastAPI-service die inkomende facturen classificeert met Claude.
  Proof-of-concept voor het finance-team.
type: app
runtime: python-serverless
stack: [fastapi, anthropic]
owner: niek
deploy: true
url: https://cookbook-invoice-classifier.vercel.app
tags: [llm, finance]
```
