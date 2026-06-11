# Index-site

Next.js-catalogus die bij build alle `../cookbooks/*/cookbook.yaml` leest en rendert.

## Lokaal

```bash
npm install
npm run dev        # http://localhost:3000
npm run validate   # manifest-validatie (zelfde check als CI)
```

## Vercel-setup (eenmalig)

1. Vercel-dashboard → Handpicked-team → Add New… → Project → deze repo.
2. **Root Directory**: `index`
3. **Ignored Build Step** (Settings → Git), zodat alleen relevante wijzigingen builden:
   ```bash
   git diff HEAD^ HEAD --quiet -- . ../cookbooks ':!../cookbooks/*/src'
   ```
   (Manifest- of index-wijzigingen → rebuild; code-wijzigingen binnen een cookbook-`src/` niet.)

## Schema wijzigen?

Het manifest-schema leeft op vier plekken die samen moeten blijven lopen: `scripts/validate.mjs`, `templates/cookbook.yaml`, `lib/cookbooks.ts` en de README's. Wijzig ze in één PR.
