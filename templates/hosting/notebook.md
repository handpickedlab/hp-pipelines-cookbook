# HOSTING — notebook

Notebooks worden niet als server gehost. Twee smaken:

## Smaak A — statisch (Jupyter, read-only)

De bron-notebook staat in `src/`. Render hem naar HTML en commit het resultaat mee, zodat de catalogus ernaar kan linken zonder runtime:

```bash
jupyter nbconvert --to html src/notebook.ipynb --output-dir src/dist
```

Zet daarna het pad of de gepubliceerde URL in `cookbook.yaml` onder `url:`.

## Smaak B — interactief (marimo → WASM)

marimo exporteert naar een statisch HTML-bestand waarin Python client-side draait via Pyodide. Geen server, geen kosten; beperkt tot pure-Python packages (numpy/pandas/matplotlib werken).

```bash
marimo export html-wasm src/notebook.py -o src/dist --mode run
```

Het resultaat in `src/dist/` is statisch en kan desgewenst als eigen Vercel-project gehost worden (root directory `cookbooks/<slug>/src/dist`, zet dan `deploy: true`) — of gewoon gelinkt vanuit de index.

## Checklist

- [ ] Bron-notebook én gerenderde output allebei in `src/`
- [ ] Output opnieuw gerenderd na laatste wijziging (geen stale HTML)
- [ ] Geen secrets/API-keys in cellen of output
