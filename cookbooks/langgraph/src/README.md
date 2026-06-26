# LangGraph — writer-benchmark

LangGraph-implementatie van de **vaste schrijf-casus**: een LinkedIn-artikel-pipeline
met de rollen Writer → Editor → Reviewer → Orchestrator (revisie-loop) → HITL. Python +
OpenAI. Drie oplopende niveaus, dezelfde input elke run — zo is het framework de enige
variabele in een vergelijking met andere agent-pipeline-tools.

> De casus zelf (briefing + output-preferences) staat hard in [`inputs.py`](inputs.py) en
> verandert niet per framework. Pas die niet aan voor een eerlijke vergelijking.

## De casus in het kort

- **Briefing**: LinkedIn-artikel over Handpickeds interne pipeline-tool, doelgroep B2B-marketeers.
- **Output preferences**: 600 woorden, Nederlands, confident/niet-hypey, vaste structuur,
  `must_include` (1 voorbeeld + 1 CTA) en `must_avoid` (geen em-dashes, "revolutionair",
  "game-changer", "disruptief").
- **Agents**: Writer schrijft → Editor verbetert + dwingt preferences af → Reviewer geeft
  `{ "pass": bool, "reason": str }` → Orchestrator stuurt de revisie-loop (max 3 iteraties)
  → HITL pauzeert na geslaagde review voor menselijke approval.
- **Output per run**: finale copy + volledige historie (elke draft, elke review,
  iteratie-teller, approval-besluit) als JSON UI-payload.

## Niveaus

| Niveau | Bestand | Wat draait | Status |
|---|---|---|---|
| **L1** Writer | `l1_writer.py` | alleen Writer | ✅ |
| **L2** Lineaire chain | `l2_chain.py` | Writer → Editor → Reviewer | ✅ |
| **L3** Orchestrator + HITL | `l3_orchestrator.py` | revisie-loop (max 3) + HITL + checkpointing | ✅ |

## Setup

```bash
cp .env.example .env        # vul OPENAI_API_KEY in
```

OpenAI-key haal je bij [platform.openai.com](https://platform.openai.com/api-keys).
Model is overridebaar via `OPENAI_MODEL` (default `gpt-5.4-mini`).

## Runnen — CLI

```bash
./start.sh                  # L1 (default)
./start.sh l2               # Writer → Editor → Reviewer
./start.sh l3               # revisie-loop + HITL prompt in terminal
./start.sh l3 -- --auto-approve   # L3 smoke test zonder HITL prompt
```

Of handmatig:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python l2_chain.py
python l3_orchestrator.py --auto-approve
```

## Runnen — web-UI (serverless)

Een FastAPI-app (`api/index.py`) draait dezelfde pipeline en toont het resultaat in de
browser. Lokaal:

```bash
pip install -r requirements.txt uvicorn
uvicorn api.index:app --reload      # http://localhost:8000
```

Op Vercel staat dit als serverless function achter de wachtwoord-gate (zie `HOSTING.md`).
**L3 draait in de web-UI in auto-approve** — de echte HITL-pauze werkt alleen via de CLI,
want serverless is stateless en houdt de `interrupt()`-checkpoint niet vast tussen requests.

De UI heeft een **input-paneel** (briefing + preferences, voorgevuld met de vaste casus —
overschrijfbaar) en een **observability-kaart**: per run de LLM-calls, latency en
token-counts (totaal + per node). Zet de `LANGSMITH_*` env-vars voor volledige
prompt/response-traces in LangSmith. Endpoints: `GET /api/defaults` (casus voor het formulier),
`POST /run` (`{level, briefing, preferences}`), `GET /api/health` (model + tracing-status).

## Structuur

- `inputs.py` — vaste briefing + output preferences (de casus).
- `common.py` — gedeelde Pydantic-modellen, LLM-setup, de lokale validatie-gate en de
  Writer/Editor/Reviewer nodes. **Framework-agnostisch** op de LangChain-LLM-call na —
  goede basis om voor PydanticAI / LlamaIndex te hergebruiken.
- `l1_writer.py` — één Writer-node.
- `l2_chain.py` — lineaire chain; print JSON UI-payload na afloop.
- `l3_orchestrator.py` — revisie-loop (max 3 iteraties), checkpointing, HITL via `interrupt()`.
- `api/index.py` + `api/_ui.py` — de serverless web-UI (FastAPI + HTML), draait dezelfde pipeline.
- `middleware.ts` / `vercel.json` — wachtwoord-gate en routing voor de Vercel-deploy.

## L3 — HITL & checkpointing

Na een geslaagde review pauzeert de graph bij de `hitl`-node. In de terminal kies je
goedkeuring of stuur je terug met feedback. De run hervat via checkpointing
(`InMemorySaver`) zonder opnieuw te starten. Voor geautomatiseerde runs: `--auto-approve`.

De Reviewer heeft een **lokale validatie-gate** (`must_avoid_violations` + woordtelling-
venster in `common.py`): faalt lengte of een verboden term, dan wordt de review
deterministisch op `pass=false` gezet — voorkomt vals-positieve LLM-reviews.

## Findings (LangGraph)

Gemeten op **`gpt-5.4-mini`** (reasoning-model, geen custom temperature). De mechaniek
van alle drie de niveaus is geverifieerd; L3 is end-to-end gedraaid.

> **Modelkeuze is de gevoelige variabele op deze casus (lengte).** Met `gpt-4o-mini`
> bleef de output rond ~300 woorden steken (ruim onder het 540-660-venster) en de Editor
> corrigeerde dat niet → de loop haalde nooit een pass en liep elke keer tot
> `max_iterations`. Met `gpt-5.4-mini` houdt het model de lengte-instructie wél aan en
> passeert de loop. Eerste benchmark-observatie genoteerd.

**L1** Writer — 👌 Eén node, Pydantic structured output, trace in state. Op `gpt-5.4-mini`
landt de Writer rond/iets boven target; op `gpt-4o-mini` te kort. 👎 Geen UI. Effort: laag.
*(Standalone L1-run op OpenAI nog te doen; cijfers komen nu uit de L3-run.)*

**L2** Writer → Editor → Reviewer — ✅ Drie stappen expliciet geketend, tussendrafts
zichtbaar, JSON-payload klaar voor frontend. 👎 Drie sequentiële LLM-calls; reasoning =
trager per call. Effort: medium. *(Standalone L2-run op OpenAI nog te doen.)*

**L3** Orchestrator + revisie-loop + HITL — ✅ **end-to-end geverifieerd op `gpt-5.4-mini`**.
Voorbeeldrun: iter 1 = 670 woorden → review FAIL (net boven de marge) → revisie → iter 2
= 601 woorden → review PASS → HITL approve. 2/3 iteraties, `stopped_reason: hitl_approved`.
👌 Revisie-loop werkt echt (Writer krijgt de faal-reason mee en corrigeert); guard op 3
iteraties; `interrupt()` + checkpointing; volledige historie in JSON; lokale
lengte/must_avoid-gate voorkomt vals-positieve reviews. 👎 HITL via terminal (geen Studio);
geen retry bij API-fouten; LangGraph waarschuwt over toekomstige msgpack-registratie voor
custom Pydantic types (`common.Article`/`ReviewResult`). Nog te onderzoeken: het 3×-fail-pad,
rate-limit/retry, en een handmatige (niet-`--auto-approve`) HITL-resume. Effort: medium-hoog.
