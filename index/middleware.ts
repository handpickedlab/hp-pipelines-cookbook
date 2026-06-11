// Basic-auth voor de hele catalogus. Wachtwoord komt uit de env var
// SITE_PASSWORD (Vercel project settings); zonder die var (lokaal) is de site open.
export const config = { matcher: "/(.*)" };

export default function middleware(request: Request) {
  const expected = process.env.SITE_PASSWORD;
  if (!expected) return;

  const auth = request.headers.get("authorization") ?? "";
  if (auth.startsWith("Basic ")) {
    const decoded = atob(auth.slice(6));
    const password = decoded.slice(decoded.indexOf(":") + 1);
    if (password === expected) return;
  }

  return new Response("Wachtwoord vereist", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Handpicked Cookbooks"' },
  });
}
