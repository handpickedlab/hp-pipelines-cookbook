// Wachtwoord-gate voor de hele catalogus. In plaats van de kale browser-
// basic-auth-popup toont dit een nette eigen loginpagina en onthoudt de
// toegang in een cookie. Wachtwoord komt uit de env var SITE_PASSWORD
// (Vercel project settings); zonder die var (lokaal) is de site open.
export const config = { matcher: "/((?!_next/|favicon.ico).*)" };

const COOKIE = "hp_gate";
const MAX_AGE = 60 * 60 * 24 * 30; // 30 dagen

export default async function middleware(request: Request) {
  const expected = process.env.SITE_PASSWORD;
  if (!expected) return; // geen wachtwoord ingesteld → open (lokaal)

  // Al ingelogd? Cookie bevat het wachtwoord; check tegen de actuele env var.
  const cookie = request.headers.get("cookie") ?? "";
  const current = cookie.match(/(?:^|;\s*)hp_gate=([^;]*)/)?.[1];
  if (current && safeEqual(decodeURIComponent(current), expected)) return;

  // Inzending van het formulier (POST met het wachtwoord).
  if (request.method === "POST") {
    const form = await request.formData().catch(() => null);
    const submitted = form?.get("password");
    if (typeof submitted === "string" && safeEqual(submitted, expected)) {
      const headers = new Headers({ Location: request.url });
      headers.append(
        "Set-Cookie",
        `${COOKIE}=${encodeURIComponent(expected)}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${MAX_AGE}`,
      );
      return new Response(null, { status: 303, headers });
    }
    return gate(true); // verkeerd wachtwoord
  }

  return gate(false);
}

// Constante-tijd vergelijking, voorkomt timing-lekjes.
function safeEqual(a: string, b: string) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function gate(error: boolean) {
  return new Response(page(error), {
    status: error ? 401 : 200,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function page(error: boolean) {
  return `<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="robots" content="noindex" />
<title>Handpicked Cookbooks</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 100vh; display: grid; place-items: center;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    background: #0b0d12; color: #e7e9ee; padding: 24px;
  }
  .card {
    width: 100%; max-width: 360px; background: #14171f; border: 1px solid #232733;
    border-radius: 16px; padding: 32px 28px; box-shadow: 0 20px 60px rgba(0,0,0,.45);
  }
  .logo { font-size: 28px; margin: 0 0 4px; }
  h1 { font-size: 18px; margin: 0 0 4px; font-weight: 600; }
  p { margin: 0 0 20px; color: #9aa1b1; font-size: 14px; line-height: 1.4; }
  label { display: block; font-size: 13px; color: #9aa1b1; margin: 0 0 6px; }
  input {
    width: 100%; padding: 11px 13px; border-radius: 10px; border: 1px solid #2b303d;
    background: #0e1117; color: #e7e9ee; font-size: 15px; outline: none;
  }
  input:focus { border-color: #5b8cff; box-shadow: 0 0 0 3px rgba(91,140,255,.25); }
  button {
    width: 100%; margin-top: 16px; padding: 11px; border: 0; border-radius: 10px;
    background: #5b8cff; color: #fff; font-size: 15px; font-weight: 600; cursor: pointer;
  }
  button:hover { background: #4a7bf0; }
  .error { color: #ff8a8a; font-size: 13px; margin: 12px 0 0; ${error ? "" : "display:none;"} }
</style>
</head>
<body>
  <form class="card" method="POST" autocomplete="off">
    <div class="logo">🍳</div>
    <h1>Handpicked Cookbooks</h1>
    <p>Deze omgeving is afgeschermd. Voer het teamwachtwoord in.</p>
    <label for="password">Wachtwoord</label>
    <input id="password" name="password" type="password" autofocus required />
    <button type="submit">Toegang</button>
    <p class="error">Onjuist wachtwoord — probeer opnieuw.</p>
  </form>
</body>
</html>`;
}
