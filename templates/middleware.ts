// Basic-auth voor je cookbook — kopieer dit bestand naar cookbooks/<slug>/src/middleware.ts.
//
// Vercel Routing Middleware is framework-agnostisch: dit werkt voor Next.js,
// statische sites én Python-projecten, zonder dependencies. De provisioning-
// workflow zet de env var SITE_PASSWORD automatisch op nieuwe projecten;
// zonder die var (bv. lokaal) is de site gewoon open.
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
