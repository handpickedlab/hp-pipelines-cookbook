"""De web-UI als losse HTML-string.

Bewust een .py-module (geen .html): Python-bestanden worden altijd meegebundeld
in de Vercel-function, een los static bestand niet per se (de catch-all rewrite
stuurt alles naar de function, dus er is geen static serving).
"""

HTML = r"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="robots" content="noindex" />
<title>PydanticAI — writer-benchmark</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 100vh;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    background: #0b0d12; color: #e7e9ee; line-height: 1.5;
  }
  .wrap { max-width: 880px; margin: 0 auto; padding: 32px 20px 80px; }
  header h1 { font-size: 22px; margin: 0 0 4px; }
  header p { margin: 0 0 8px; color: #9aa1b1; font-size: 14px; }
  header code { background: #14171f; padding: 1px 6px; border-radius: 6px; font-size: 12px; }
  .metabar { font-size: 12px; color: #7d8496; margin: 0 0 22px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  .controls {
    display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
    background: #14171f; border: 1px solid #232733; border-radius: 14px; padding: 16px; margin-bottom: 8px;
  }
  .levels { display: flex; gap: 6px; }
  .levels button {
    background: #0e1117; color: #c7ccd8; border: 1px solid #2b303d; border-radius: 9px;
    padding: 8px 14px; font-size: 14px; cursor: pointer; font-weight: 600;
  }
  .levels button.active { background: #5b8cff; color: #fff; border-color: #5b8cff; }
  .run {
    margin-left: auto; background: #5b8cff; color: #fff; border: 0; border-radius: 9px;
    padding: 9px 20px; font-size: 14px; font-weight: 600; cursor: pointer;
  }
  .run:disabled { opacity: .5; cursor: default; }
  .hint { font-size: 12.5px; color: #7d8496; margin: 0 0 18px; }

  details.input { background: #14171f; border: 1px solid #232733; border-radius: 14px; padding: 0 18px; margin-bottom: 18px; }
  details.input > summary { cursor: pointer; padding: 16px 0; font-size: 14px; font-weight: 600; color: #c7ccd8; list-style: none; }
  details.input > summary::-webkit-details-marker { display: none; }
  details.input > summary::before { content: "▸ "; color: #7d8496; }
  details.input[open] > summary::before { content: "▾ "; }
  .form { padding: 0 0 18px; display: grid; gap: 14px; }
  .form label { display: block; font-size: 12.5px; color: #9aa1b1; margin: 0 0 5px; }
  .form input, .form textarea {
    width: 100%; padding: 9px 11px; border-radius: 9px; border: 1px solid #2b303d;
    background: #0e1117; color: #e7e9ee; font-size: 14px; outline: none; font-family: inherit; resize: vertical;
  }
  .form input:focus, .form textarea:focus { border-color: #5b8cff; box-shadow: 0 0 0 3px rgba(91,140,255,.2); }
  .row2 { display: grid; grid-template-columns: 1fr 2fr; gap: 14px; }
  .row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; }
  .reset { background: none; border: 0; color: #5b8cff; font-size: 12.5px; cursor: pointer; padding: 0; justify-self: start; }
  @media (max-width: 620px) { .row2, .row3 { grid-template-columns: 1fr; } }

  .status { font-size: 14px; color: #9aa1b1; margin: 16px 0; min-height: 20px; }
  .status .spin { display: inline-block; animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .err { color: #ff8a8a; }
  .card { background: #14171f; border: 1px solid #232733; border-radius: 14px; padding: 20px; margin: 14px 0; }
  .card h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .06em; color: #7d8496; margin: 0 0 12px; }
  .badges { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 14px; }
  .badge { font-size: 12px; padding: 3px 10px; border-radius: 999px; border: 1px solid #2b303d; color: #c7ccd8; }
  .badge.ok { background: rgba(74,222,128,.12); border-color: rgba(74,222,128,.4); color: #86efac; }
  .badge.bad { background: rgba(255,138,138,.12); border-color: rgba(255,138,138,.4); color: #ff9b9b; }
  .title { font-size: 18px; font-weight: 700; margin: 0 0 10px; }
  .prose { white-space: pre-wrap; font-size: 14.5px; color: #d6dae3; }
  .review { border-left: 3px solid #2b303d; padding: 6px 0 6px 12px; margin: 8px 0; font-size: 14px; }
  .review.pass { border-color: #4ade80; }
  .review.fail { border-color: #ff8a8a; }
  .review .reason { color: #9aa1b1; font-size: 13px; }
  details.draftwrap { margin: 8px 0; }
  details.draftwrap > summary { cursor: pointer; color: #9aa1b1; font-size: 13.5px; }
  .draft { border-top: 1px solid #232733; padding: 12px 0; }
  .draft .meta { font-size: 12.5px; color: #7d8496; margin-bottom: 6px; }
  table.trace { width: 100%; border-collapse: collapse; font-size: 13px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  table.trace th, table.trace td { text-align: left; padding: 5px 8px; border-bottom: 1px solid #1d212b; }
  table.trace th { color: #7d8496; font-weight: 600; }
  table.trace td.num { text-align: right; color: #c7ccd8; }
  .obs-note { font-size: 12px; color: #7d8496; margin: 12px 0 0; }
  .obs-note code { background: #0e1117; padding: 1px 5px; border-radius: 5px; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🔷 PydanticAI — writer-benchmark</h1>
    <p>Geef je eigen briefing of draai de vaste casus. <code>Writer → Editor → Reviewer → Orchestrator + HITL</code>.</p>
    <p class="metabar" id="metabar">…</p>
  </header>

  <details class="input" open>
    <summary>Input &amp; preferences</summary>
    <div class="form">
      <div>
        <label for="briefing">Briefing</label>
        <textarea id="briefing" rows="5" placeholder="Waar moet het artikel over gaan?"></textarea>
      </div>
      <div class="row2">
        <div>
          <label for="p_length">Lengte (woorden)</label>
          <input id="p_length" type="number" min="50" step="10" value="600" />
        </div>
        <div>
          <label for="p_tone">Toon</label>
          <input id="p_tone" type="text" />
        </div>
      </div>
      <div class="row3">
        <div>
          <label for="p_include">Must include (één per regel)</label>
          <textarea id="p_include" rows="4"></textarea>
        </div>
        <div>
          <label for="p_avoid">Must avoid (één per regel)</label>
          <textarea id="p_avoid" rows="4"></textarea>
        </div>
        <div>
          <label for="p_structure">Structuur (één per regel)</label>
          <textarea id="p_structure" rows="4"></textarea>
        </div>
      </div>
      <button class="reset" id="reset" type="button">↺ terug naar de standaard-casus</button>
    </div>
  </details>

  <div class="controls">
    <div class="levels" id="levels">
      <button data-level="l1">L1 · Writer</button>
      <button data-level="l2" class="active">L2 · Chain</button>
      <button data-level="l3">L3 · Loop + HITL</button>
    </div>
    <button class="run" id="run">Genereer</button>
  </div>
  <p class="hint" id="hint"></p>

  <div class="status" id="status"></div>
  <div id="out"></div>
</div>

<script>
  const HINTS = {
    l1: "L1 — alleen de Writer. Eén LLM-call, snelste run.",
    l2: "L2 — Writer → Editor → Reviewer, lineair. Drie calls.",
    l3: "L3 — volledige revisie-loop (max 3) + HITL (hier auto-approve). Tot 9 calls; kan met een reasoning-model even duren.",
  };
  let level = "l2";
  let DEFAULTS = null;

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const linesToArr = (s) => s.split("\n").map((x) => x.trim()).filter(Boolean);

  function setLevel(l) {
    level = l;
    for (const b of document.querySelectorAll("#levels button")) b.classList.toggle("active", b.dataset.level === l);
    $("hint").textContent = HINTS[l];
  }
  document.querySelectorAll("#levels button").forEach((b) => b.addEventListener("click", () => setLevel(b.dataset.level)));
  setLevel("l2");

  function fillForm(d) {
    $("briefing").value = d.briefing || "";
    const p = d.preferences || {};
    $("p_length").value = p.length_words != null ? p.length_words : 600;
    $("p_tone").value = p.tone || "";
    $("p_include").value = (p.must_include || []).join("\n");
    $("p_avoid").value = (p.must_avoid || []).join("\n");
    $("p_structure").value = (p.structure || []).join("\n");
  }

  async function boot() {
    try {
      const h = await (await fetch("/api/health")).json();
      $("metabar").textContent =
        "model: " + h.model +
        " · Logfire: " + (h.logfire ? "aan" : "uit") +
        (h.has_key ? "" : " · ⚠ geen API-key op de server");
    } catch (e) { $("metabar").textContent = ""; }
    try {
      DEFAULTS = await (await fetch("/api/defaults")).json();
      fillForm(DEFAULTS);
    } catch (e) {}
  }
  $("reset").addEventListener("click", () => DEFAULTS && fillForm(DEFAULTS));
  boot();

  $("run").addEventListener("click", async () => {
    const preferences = {
      length_words: Number($("p_length").value) || 600,
      tone: $("p_tone").value.trim(),
      must_include: linesToArr($("p_include").value),
      must_avoid: linesToArr($("p_avoid").value),
      structure: linesToArr($("p_structure").value),
    };
    const briefing = $("briefing").value.trim();

    $("run").disabled = true;
    $("out").innerHTML = "";
    $("status").innerHTML = '<span class="spin">⏳</span> Pipeline draait (' + level.toUpperCase() + ")…";
    const t0 = Date.now();
    try {
      const res = await fetch("/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ level, briefing, preferences }),
      });
      const data = await res.json();
      const secs = ((Date.now() - t0) / 1000).toFixed(1);
      if (!res.ok || data.error) {
        $("status").innerHTML = '<span class="err">Fout: ' + esc(data.error || res.status) + "</span>";
      } else {
        $("status").textContent = "Klaar in " + secs + "s (wall-clock).";
        render(data);
      }
    } catch (e) {
      $("status").innerHTML = '<span class="err">Netwerk-/serverfout: ' + esc(e.message) + "</span>";
    } finally {
      $("run").disabled = false;
    }
  });

  function badge(text, kind) { return '<span class="badge ' + (kind || "") + '">' + esc(text) + "</span>"; }

  function renderObs(d) {
    const t = d.totals || {};
    const b = [];
    b.push(badge((t.llm_calls || 0) + " LLM-calls"));
    if (t.duration_ms != null) b.push(badge("LLM-tijd " + (t.duration_ms / 1000).toFixed(1) + "s"));
    if (t.tokens_total != null) b.push(badge("tokens " + t.tokens_total + " (in " + (t.tokens_in != null ? t.tokens_in : "?") + " / out " + (t.tokens_out != null ? t.tokens_out : "?") + ")"));
    let html = '<div class="card"><h2>Observability</h2><div class="badges">' + b.join("") + "</div>";
    if ((d.trace || []).length) {
      html += '<table class="trace"><thead><tr><th>#</th><th>node</th><th>iter</th><th>ms</th><th>tokens</th></tr></thead><tbody>';
      d.trace.forEach((c, i) => {
        html += "<tr><td class='num'>" + (i + 1) + "</td><td>" + esc(c.node) + "</td><td class='num'>" + (c.iteration != null ? c.iteration : "") +
          "</td><td class='num'>" + (c.duration_ms != null ? c.duration_ms : "") + "</td><td class='num'>" + (c.tokens_total != null ? c.tokens_total : "") + "</td></tr>";
      });
      html += "</tbody></table>";
    }
    html += '<p class="obs-note">Volledige prompt/response-waterfall per run: zet <code>LOGFIRE_TOKEN</code> (zie HOSTING.md), dan logt elke call naar Pydantic Logfire.</p>';
    html += "</div>";
    return html;
  }

  function render(d) {
    const fc = d.final_copy || {};
    const out = [];

    out.push(renderObs(d));

    // Finale copy
    const meta = [];
    meta.push(badge(d.level));
    if (d.iteration_count != null) meta.push(badge("iteraties: " + d.iteration_count + (d.max_iterations ? " / " + d.max_iterations : "")));
    if (d.stopped_reason) meta.push(badge("gestopt: " + d.stopped_reason, d.stopped_reason === "hitl_approved" ? "ok" : "bad"));
    if (d.auto_approved) meta.push(badge("HITL: auto-approve"));

    out.push('<div class="card">');
    out.push("<h2>Finale copy</h2>");
    out.push('<div class="badges">' + meta.join("") + "</div>");
    const fcb = [];
    fcb.push(badge(fc.word_count + " woorden", fc.within_length_target ? "ok" : "bad"));
    fcb.push(badge(fc.within_length_target ? "binnen lengte-target" : "buiten lengte-target", fc.within_length_target ? "ok" : "bad"));
    const mav = d.must_avoid_violations || [];
    fcb.push(badge(mav.length ? "must_avoid: " + mav.join(", ") : "must_avoid: schoon", mav.length ? "bad" : "ok"));
    if (d.review_pass != null) fcb.push(badge(d.review_pass ? "review: pass" : "review: fail", d.review_pass ? "ok" : "bad"));
    out.push('<div class="badges">' + fcb.join("") + "</div>");
    out.push('<div class="title">' + esc(fc.title) + "</div>");
    out.push('<div class="prose">' + esc(fc.body_markdown) + "</div>");
    out.push("</div>");

    // Reviews
    if ((d.reviews || []).length) {
      out.push('<div class="card"><h2>Reviews</h2>');
      for (const r of d.reviews) {
        out.push('<div class="review ' + (r.pass ? "pass" : "fail") + '"><strong>iter ' + r.iteration + " — " + (r.pass ? "PASS" : "FAIL") + '</strong><div class="reason">' + esc(r.reason) + "</div></div>");
      }
      out.push("</div>");
    }

    // Drafts
    if ((d.drafts || []).length) {
      out.push('<div class="card"><h2>Tussendrafts (' + d.drafts.length + ")</h2>");
      for (const dr of d.drafts) {
        out.push('<details class="draftwrap"><summary>iter ' + dr.iteration + " · " + esc(dr.stage) + " · " + dr.word_count + " woorden</summary>");
        out.push('<div class="draft"><div class="meta">' + esc(dr.title) + '</div><div class="prose">' + esc(dr.body_markdown) + "</div></div></details>");
      }
      out.push("</div>");
    }

    $("out").innerHTML = out.join("");
  }
</script>
</body>
</html>"""
