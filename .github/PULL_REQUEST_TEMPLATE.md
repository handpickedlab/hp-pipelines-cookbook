# Cookbook PR

## Wat is dit?

<!-- Korte beschrijving van het cookbook of de wijziging. -->

## Checklist (nieuw cookbook)

- [ ] `cookbooks/<slug>/cookbook.yaml` aanwezig en ingevuld (gestart vanaf `templates/cookbook.yaml`)
- [ ] `slug` is gelijk aan de mapnaam
- [ ] `HOSTING.md` aanwezig, gebaseerd op het juiste recept uit `templates/hosting/`
- [ ] Geen secrets/credentials in de code of in exports
- [ ] `node index/scripts/validate.mjs` slaagt lokaal
- [ ] Bij `runtime: python-server`: `url:` gevuld en bereikbaar
- [ ] Bij `deploy: true`: Vercel-project aangemaakt (of afgesproken wie dat na merge doet)

## Checklist (wijziging aan index/ of templates/)

- [ ] Schema-wijziging? Validator, template, index-site én docs in deze PR bijgewerkt
