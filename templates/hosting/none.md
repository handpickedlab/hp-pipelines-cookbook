# HOSTING — none (workflows, exports, docs)

Dit cookbook wordt niet gedeployd. Het bestaat uit bestanden (bv. n8n workflow-JSON, prompts, datasets, documentatie) die anderen importeren of lezen.

## Wat hier hoort te staan

Beschrijf hoe iemand dit gebruikt, bijvoorbeeld voor een n8n-export:

1. Welke bestanden in `src/` zijn de workflows, en wat doet elk.
2. Hoe importeer je ze (n8n → Workflows → Import from File).
3. Welke credentials/omgevingsvariabelen de gebruiker zelf moet aanmaken (namen, geen waarden).
4. Eventuele volgorde of afhankelijkheden tussen workflows.

## Checklist

- [ ] Geen credentials in de exports (n8n-exports kunnen credential-referenties bevatten — check de JSON)
- [ ] Gebruiksinstructie hierboven ingevuld
- [ ] `deploy: false` en geen `url:` nodig in het manifest
