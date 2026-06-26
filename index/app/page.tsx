import { getCookbooks } from "@/lib/cookbooks";

const REPO_URL = "https://github.com/handpickedlab/hp-pipelines-cookbook";

export default function Home() {
  const cookbooks = getCookbooks();

  return (
    <main>
      <header>
        <h1>Handpicked Cookbooks</h1>
        <p className="subtitle">
          {cookbooks.length} experiment{cookbooks.length === 1 ? "" : "en"} ·{" "}
          <a href={`${REPO_URL}#een-cookbook-toevoegen`}>voeg er een toe via een PR</a>
        </p>
      </header>

      <section className="grid">
        {cookbooks.map((c) => (
          <article key={c.slug} className={`card${c.url ? " card-clickable" : ""}`}>
            {c.url && (
              <a
                className="card-link"
                href={c.url}
                target="_blank"
                rel="noreferrer"
                aria-hidden={true}
                tabIndex={-1}
              />
            )}
            <div className="card-head">
              <h2>{c.name}</h2>
              <span className={`badge badge-${c.type}`}>{c.type}</span>
            </div>
            <p>{c.description}</p>
            <dl>
              <div>
                <dt>Runtime</dt>
                <dd>{c.runtime}</dd>
              </div>
              <div>
                <dt>Stack</dt>
                <dd>{c.stack.join(", ") || "—"}</dd>
              </div>
              <div>
                <dt>Owner</dt>
                <dd>{c.owner}</dd>
              </div>
            </dl>
            {c.tags.length > 0 && (
              <div className="tags">
                {c.tags.map((t) => (
                  <span key={t} className="tag">
                    {t}
                  </span>
                ))}
              </div>
            )}
            <div className="links">
              {c.url && (
                <a href={c.url} target="_blank" rel="noreferrer">
                  Open ↗
                </a>
              )}
              <a href={`${REPO_URL}/tree/main/cookbooks/${c.slug}`} target="_blank" rel="noreferrer">
                Broncode ↗
              </a>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
