# HP Pipelines Cookbook

Eén casus, zes frameworks, dezelfde input elke keer. Deze repo vergelijkt hoe verschillende agent-pipeline tools dezelfde opdracht uitvoeren — zodat we kunnen zien waar elk framework breekt en welke we meenemen.

**Frameworks:** n8n · Dify · Pydantic AI · Mastra · LangGraph · AgentField

---

## Wat is dit?

Handpicked bouwt een interne tool waarmee agency-teams agent-pipelines kunnen hergebruiken in plaats van elke keer opnieuw te beginnen. Voordat we kiezen welk framework we standaardiseren, draaien we **dezelfde repliceerbare casus** op elk platform.

**Repliceerbaar** betekent: vaste briefing, vaste output preferences, vaste agent-rollen en vaste succescriteria. Alleen het framework verandert.

---

## Repo-structuur

| Map | Framework | Status |
|---|---|---|
| [`01_n8n/`](01_n8n/) | n8n | Docker Compose + startscript aanwezig |
| [`02_mastra/`](02_mastra/) | Mastra | — |
| [`03_langgraph/`](03_langgraph/) | LangGraph | — |
| [`04_dify/`](04_dify/) | Dify | — |
| [`05_pydanticai/`](05_pydanticai/) | Pydantic AI | — |
| [`06_agentfield/`](06_agentfield/) | AgentField | — |

Elke map bevat de implementatie van de casus op drie niveaus (L1, L2, L3). Per cel in de matrix onderaan documenteren we een verdict plus findings.

---

## Input (vast, gebruik dit elke run)

### Briefing

> Handpicked lanceert een interne tool waarmee agency-teams agent-pipelines kunnen hergebruiken in plaats van elke keer opnieuw te bouwen. We willen hier een LinkedIn-artikel over, gericht op B2B-marketeers en creatieve leads bij mid-size agencies. Doel: awareness plus een paar demo-aanvragen. We willen één concreet voorbeeld van een hergebruikte pipeline laten zien, en eindigen met een duidelijke call-to-action voor een demo. Het moet geloofwaardig en zelfverzekerd klinken, niet als marketinghype.

*(Placeholder. Vervang door je eigen lap tekst — de pipeline blijft gelijk.)*

### Output preferences (vast)

```json
{
  "format": "LinkedIn-artikel, markdown",
  "length_words": 600,
  "tone": "confident, technisch geloofwaardig, niet hypey, Nederlands",
  "structure": ["hook", "probleem", "oplossing met 1 concreet voorbeeld", "call-to-action"],
  "must_include": ["1 concreet voorbeeld", "1 call-to-action voor een demo"],
  "must_avoid": ["em-dashes", "revolutionair", "game-changer", "disruptief"]
}
```

---

## De agents (vaste rollen)

| Agent | Rol |
|---|---|
| **Writer** | Schrijft een draft op basis van de briefing en output preferences. |
| **Editor** | Verbetert structuur, lengte en leesbaarheid; dwingt output preferences af. |
| **Reviewer** | Beoordeelt tegen briefing en preferences → `{ "pass": bool, "reason": str }`. |
| **Orchestrator** | Stuurt writer, editor en reviewer aan; beheert revisie-loop bij `pass: false` (max 3 iteraties). |
| **HITL pass** | Pauzeert na geslaagde review; mens keurt goed of stuurt terug met opmerking. |

**Output van elke run:** finale copy plus volledige historie (elke draft, elke review, iteratie-teller, approval-besluit).

---

## Drie niveaus

Zelfde casus, oplopende diepte. Draai alle drie per framework.

| Niveau | Wat draait | Wat het test | Lens |
|---|---|---|---|
| **L1** | Alleen Writer | Instapdrempel, structured output, observability | PO |
| **L2** | Writer → Editor → Reviewer (lineair, één pass) | Chaining, state-passing, output naar front-end | Design |
| **L3** | Orchestrator + revisie-loop + HITL pass | Cyclus, loop-guard, interrupt + resume, human-in-the-loop | Dev |

L1 en L2 gebruiken een subset van dezelfde agents en dezelfde input. L3 is de volledige casus.

---

## Succescriteria per niveau

**L1**
- Writer levert een draft binnen de lengte.
- Output is geldige structuur.
- Input/output per call is inzichtelijk.

**L2**
- Alle drie de stappen draaien.
- Tussendrafts zijn zichtbaar.
- Finale copy respecteert output preferences (lengte, must_avoid).
- Output is naar een UI te tonen.

**L3**
- Loop stopt deterministisch op de guard (max 3 iteraties).
- Run pauzeert echt bij HITL pass en is daarna te hervatten zonder vanaf nul te draaien.
- Volledige historie is uitleesbaar.

---

## Edge-case probes (L3, per framework)

1. **Conditionele cyclus** — Reviewer faalt drie keer. Stopt de loop netjes op de guard, of loopt hij door / crasht hij?
2. **LLM time-out / rate-limit** — Forceer een failing call. Retry met backoff, of valt alles om?
3. **Approval interrupt + resume** — Pauzeert de run echt en kun je hervatten zonder herstart (checkpointing)?
4. **State-inspectie mid-run** — Kun je tussendrafts en de iteratie-teller live uitlezen?
5. **Orchestrator-controle** — Kun je aansturing aanpassen (volgorde, guard, welke agent wanneer) zonder alles te herbouwen?

---

## Vergelijkingsmatrix

Per cel: verdict plus findings (Setup-tijd, Highs 👌, Lows 👎, Nog te onderzoeken, Effort, Showcase).

| | n8n | Dify | Pydantic AI | Mastra | LangGraph | AgentField |
|---|---|---|---|---|---|---|
| **L1** Writer | | | | | | |
| **L2** Lineaire chain | | | | | | |
| **L3** Orchestrator + HITL | | | | | | |

Aan het eind zie je per framework waar het breekt en welke je meeneemt.

---

## Quick start — n8n

```bash
cd 01_n8n
docker compose up -d
# UI: http://localhost:5678
```

Of lokaal zonder Docker:

```bash
cd 01_n8n
./start.sh
```

---

## Findings-template (per cel)

```markdown
### [Framework] — L[n]

**Verdict:** ✅ / ⚠️ / ❌

| Veld | Notitie |
|---|---|
| Setup-tijd | |
| Highs 👌 | |
| Lows 👎 | |
| Nog te onderzoeken | |
| Effort | |
| Showcase | |
```
