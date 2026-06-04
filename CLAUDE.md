# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Wat dit is

Een vergelijkings-cookbook: **één vaste casus, zes agent-pipeline frameworks** (n8n, Mastra, LangGraph, Dify, Pydantic AI, AgentField). Handpicked wil één framework standaardiseren voor herbruikbare agent-pipelines en draait daarom dezelfde repliceerbare casus op elk platform om te zien waar elk breekt.

Het werk is een matrix: framework × niveau (L1/L2/L3). Elke cel krijgt een verdict + findings. De repo is grotendeels lege scaffolding — alleen `01_n8n/` heeft een runnable setup. De rest zijn lege framework-mappen met een `.gitkeep`.

## De vaste casus (verandert nooit — alleen het framework verandert)

De input is hard vastgelegd in `README.md` en moet bij elke run identiek zijn:
- **Briefing**: LinkedIn-artikel over Handpickeds interne pipeline-tool, B2B-marketeers als doelgroep.
- **Output preferences** (JSON in README): 600 woorden, Nederlands, confident/niet-hypey, vaste structuur, `must_include` en `must_avoid` (geen em-dashes, geen "revolutionair"/"game-changer"/"disruptief").
- **Agents (vaste rollen)**: Writer → Editor → Reviewer (geeft `{ "pass": bool, "reason": str }`) → Orchestrator (revisie-loop, **max 3 iteraties**) → HITL pass (pauzeert na geslaagde review voor menselijke approval).
- **Output per run**: finale copy + volledige historie (elke draft, elke review, iteratie-teller, approval-besluit).

Bij implementeren: lees de exacte briefing, preferences en rollen uit `README.md` — niet uit deze samenvatting overschrijven.

## Drie niveaus (per framework alle drie bouwen)

- **L1** — alleen Writer. Test: instapdrempel, structured output, observability.
- **L2** — Writer → Editor → Reviewer, lineair, één pass. Test: chaining, state-passing, output naar UI.
- **L3** — Orchestrator + revisie-loop + HITL. Test: cyclus, loop-guard (deterministisch stoppen op 3), interrupt + resume via checkpointing, state-inspectie mid-run.

L3 is de volledige casus; L1/L2 zijn subsets met dezelfde input. Edge-case probes voor L3 staan in `README.md` (conditionele cyclus, time-out/rate-limit, approval interrupt+resume, state-inspectie, orchestrator-controle) — gebruik die als acceptatietests.

## Structuur & conventies

Genummerde mappen, één per framework: `01_n8n/`, `02_mastra/`, `03_langgraph/`, `04_dify/`, `05_pydanticai/`, `06_agentfield/`. Elke map is zelfstandig — eigen runtime, dependencies en startcommando per framework. Er is (nog) geen gedeelde toplaag-toolchain.

Werk je aan één framework, blijf dan binnen die map. Volg het `01_n8n/`-patroon als referentie: een minimale, self-contained setup (`docker-compose.yml` + `start.sh`) die met één commando draait.

## Runnen

n8n (enige werkende setup):
```bash
cd 01_n8n
docker compose up -d        # UI op http://localhost:5678
# of lokaal zonder Docker:
./start.sh
```

Voor andere frameworks bestaat nog geen runcommando — dat hoort onderdeel te zijn van wat je voor die map bouwt.

## Findings vastleggen

Na een implementatie: vul de cel in de vergelijkingsmatrix in `README.md` en gebruik de findings-template onderaan `README.md` (Verdict ✅/⚠️/❌ + Setup-tijd, Highs, Lows, Nog te onderzoeken, Effort, Showcase). Dit is het eigenlijke deliverable van de repo, niet alleen de code.
