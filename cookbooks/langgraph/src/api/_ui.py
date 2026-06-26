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
<title>LangGraph — writer-benchmark</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 100vh;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    background: #0b0d12; color: #e7e9ee; line-height: 1.5;
  }
  .wrap { max-width: 860px; margin: 0 auto; padding: 32px 20px 80px; }
  header h1 { font-size: 22px; margin: 0 0 4px; }
  header p { margin: 0 0 24px; color: #9aa1b1; font-size: 14px; }
  header code { background: #14171f; padding: 1px 6px; border-radius: 6px; font-size: 12px; }
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
  .hint { font-size: 12.5px; color: #7d8496; margin: 0 0 24px; }
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
  details { margin: 8px 0; }
  summary { cursor: pointer; color: #9aa1b1; font-size: 13.5px; }
  .draft { border-top: 1px solid #232733; padding: 12px 0; }
  .draft .meta { font-size: 12.5px; color: #7d8496; margin-bottom: 6px; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip { font-size: 11.5px; background: #0e1117; border: 1px solid #2b303d; border-radius: 6px; padding: 2px 7px; color: #9aa1b1; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🕸️ LangGraph — writer-benchmark</h1>
    <p>Vaste casus, vast framework. <code>Writer → Editor → Reviewer → Orchestrator + HITL</code>. Kies een niveau en draai de pipeline.</p>
  </header>

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

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  function setLevel(l) {
    level = l;
    for (const b of document.querySelectorAll("#levels button")) b.classList.toggle("active", b.dataset.level === l);
    $("hint").textContent = HINTS[l];
  }
  document.querySelectorAll("#levels button").forEach((b) => b.addEventListener("click", () => setLevel(b.dataset.level)));
  setLevel("l2");

  $("run").addEventListener("click", async () => {
    $("run").disabled = true;
    $("out").innerHTML = "";
    $("status").innerHTML = '<span class="spin">⏳</span> Pipeline draait (' + level.toUpperCase() + ")…";
    const t0 = Date.now();
    try {
      const res = await fetch("/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ level }),
      });
      const data = await res.json();
      const secs = ((Date.now() - t0) / 1000).toFixed(1);
      if (!res.ok || data.error) {
        $("status").innerHTML = '<span class="err">Fout: ' + esc(data.error || res.status) + "</span>";
      } else {
        $("status").textContent = "Klaar in " + secs + "s.";
        render(data);
      }
    } catch (e) {
      $("status").innerHTML = '<span class="err">Netwerk-/serverfout: ' + esc(e.message) + "</span>";
    } finally {
      $("run").disabled = false;
    }
  });

  function badge(text, kind) { return '<span class="badge ' + (kind || "") + '">' + esc(text) + "</span>"; }

  function render(d) {
    const fc = d.final_copy || {};
    const out = [];

    // Meta
    const meta = [];
    meta.push(badge(d.level));
    if (d.iteration_count != null) meta.push(badge("iteraties: " + d.iteration_count + (d.max_iterations ? " / " + d.max_iterations : "")));
    if (d.stopped_reason) meta.push(badge("gestopt: " + d.stopped_reason, d.stopped_reason === "hitl_approved" ? "ok" : "bad"));
    if (d.auto_approved) meta.push(badge("HITL: auto-approve"));

    // Final copy
    out.push('<div class="card">');
    out.push('<h2>Finale copy</h2>');
    out.push('<div class="badges">' + meta.join("") + "</div>");
    const fcBadges = [];
    fcBadges.push(badge(fc.word_count + " woorden", fc.within_length_target ? "ok" : "bad"));
    fcBadges.push(badge(fc.within_length_target ? "binnen lengte-target" : "buiten lengte-target", fc.within_length_target ? "ok" : "bad"));
    const mav = d.must_avoid_violations || [];
    fcBadges.push(badge(mav.length ? "must_avoid: " + mav.join(", ") : "must_avoid: schoon", mav.length ? "bad" : "ok"));
    if (d.review_pass != null) fcBadges.push(badge(d.review_pass ? "review: pass" : "review: fail", d.review_pass ? "ok" : "bad"));
    out.push('<div class="badges">' + fcBadges.join("") + "</div>");
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
        out.push("<details><summary>iter " + dr.iteration + " · " + esc(dr.stage) + " · " + dr.word_count + " woorden</summary>");
        out.push('<div class="draft"><div class="meta">' + esc(dr.title) + '</div><div class="prose">' + esc(dr.body_markdown) + "</div></div></details>");
      }
      out.push("</div>");
    }

    // Trace
    if ((d.trace_nodes || []).length) {
      out.push('<div class="card"><h2>Trace</h2><div class="chips">');
      out.push(d.trace_nodes.map((n) => '<span class="chip">' + esc(n) + "</span>").join(""));
      out.push("</div></div>");
    }

    $("out").innerHTML = out.join("");
  }
</script>
</body>
</html>"""
