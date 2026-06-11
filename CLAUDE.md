# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Wat dit is

Een monorepo met onafhankelijk deploybare **cookbooks** (experimenten van het Handpicked-team) plus een centrale catalogus-site. Geen klassieke monorepo: er is géén gedeelde toolchain over cookbooks heen. Elk cookbook onder `cookbooks/<slug>/` is zelfstandig — eigen stack, eigen dependencies, eigen hosting.

De lijm is de manifest-laag: elk cookbook heeft een `cookbook.yaml` (schema: zie `index/scripts/validate.mjs`) en een `HOSTING.md`. De index-site (`index/`, Next.js) leest bij build alle manifests en rendert de catalogus.

## Conventies

- **Slug = mapnaam.** Kebab-case, en het `slug`-veld in `cookbook.yaml` moet exact gelijk zijn aan de mapnaam. De validator dwingt dit af.
- **Werk je aan één cookbook, blijf in die map.** Raak `index/` alleen aan voor catalogus-features, niet voor cookbook-specifieke zaken.
- **Nieuw cookbook**: start vanaf `templates/cookbook.yaml` en het juiste `templates/hosting/<runtime>.md`-recept. Verzin geen eigen manifest-velden zonder de validator én de index-site mee te updaten.
- **Runtime bepaalt hosting**: `node` en `python-serverless` krijgen een eigen Vercel-project; `python-server` is extern (URL in manifest); `notebook` wordt statisch; `none` wordt niet gedeployd.

## Commando's

```bash
cd index && npm install && npm run dev   # catalogus lokaal op :3000
node index/scripts/validate.mjs          # alle manifests valideren (draait ook in CI)
```

## CI

`.github/workflows/validate.yml` draait de manifest-validatie op elke PR. Als je het manifest-schema wijzigt: validator, template (`templates/cookbook.yaml`), index-site en deze docs in dezelfde PR bijwerken.
