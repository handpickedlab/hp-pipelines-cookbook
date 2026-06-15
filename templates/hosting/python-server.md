# HOSTING — python-server (Streamlit/Gradio/Dash, extern gehost)

Dit cookbook heeft een persistent Python-process nodig en draait dus **niet** op Vercel. Het wordt extern gehost; de catalogus linkt naar de URL uit het manifest.

> ⚠️ **Geen gedeelde wachtwoord-gate.** De `SITE_PASSWORD`-gate (`templates/middleware.ts`) is Vercel-middleware en draait alleen vóór op-Vercel-gehoste cookbooks. Omdat dit extern draait, beschermt die gate je app **niet** — `middleware.ts` kopiëren heeft hier geen effect. Wil je je app afschermen, regel dan auth op de host zelf (bv. Streamlit-authenticatie, een HF Spaces private Space, of basic-auth/SSO op Railway/Fly).

## Lokaal draaien

```bash
cd src
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py          # of jouw equivalent
```

## Hosting-opties

| Optie | Wanneer |
|---|---|
| **Hugging Face Spaces** | Default: gratis, nul setup. Let op: publiek tenzij betaald plan. |
| **Railway / Fly.io / Render** | Als het privé moet of meer controle nodig is. Kost geld; overleg met je team-lead voordat je een nieuw account/platform introduceert. |

## Na het deployen

1. Zet de live URL in `cookbook.yaml` onder `url:` — **verplicht** voor deze runtime, de validator checkt erop.
2. `deploy:` blijft `false` (er is geen Vercel-project); de index gebruikt `url:` als link.
3. Documenteer hieronder waar het draait, onder welk account, en hoe je redeployt.

## Waar draait dit?

- Platform:
- Account/workspace:
- Redeploy-procedure:

## Checklist

- [ ] `url:` gevuld en bereikbaar
- [ ] Geen secrets in de repo
- [ ] Redeploy-procedure hierboven ingevuld
