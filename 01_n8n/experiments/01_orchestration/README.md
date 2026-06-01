# Experiment 01: Multi-Agent Orchestration

A writing pipeline built in n8n where one **Orchestrator** agent coordinates three specialist agents — **Writer**, **Editor**, and **Reviewer** — using n8n's built-in MCP server to discover and invoke workflows.

## Goal

Explore whether n8n can act as a lightweight agent orchestration layer: one top-level agent that plans and delegates work to sub-workflows exposed as MCP tools, instead of wiring everything into a single monolithic workflow.

## Architecture

```
┌─────────────────────┐
│  Form submission    │  Briefing (textarea)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     MCP tools (list + execute workflows)
│  Orchestrator Agent │ ───────────────────────────────────────► n8n MCP server
└──────────┬──────────┘
           │  Writer → Editor → Reviewer (linear, 1 pass)
           ▼
┌──────────┴──────────┬──────────────────┬──────────────────┐
│   Writer Agent      │   Editor Agent   │  Reviewer Agent  │
│   (draft)           │   (polish)       │  (pass / fail)   │
└─────────────────────┴──────────────────┴──────────────────┘
```

| Workflow | Trigger | Role |
|----------|---------|------|
| **Orchestrator Agent** | Form | Lists available MCP workflows, then runs Writer → Editor → Reviewer in order |
| **Writer Agent** | Webhook | Produces a first draft from the briefing and output preferences |
| **Editor Agent** | Webhook | Improves structure, length, and readability |
| **Reviewer Agent** | Webhook | Checks output against the briefing; returns `{ "pass": true/false, "reason": "..." }` |

All four workflows use **GPT-5 mini** via the OpenAI Chat Model node.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (recommended), or Node.js for running n8n locally
- An [OpenAI API key](https://platform.openai.com/api-keys)
- n8n with LangChain agent nodes (included in recent n8n releases)

## Run n8n

From the `01_n8n` directory:

**Docker (recommended)**

```bash
docker compose up -d
```

Open [http://localhost:5678](http://localhost:5678).

**Local CLI**

```bash
./start.sh
```

This sets `N8N_USER_FOLDER` to `./n8n_data` and starts n8n on port 5678.

## Setup

### 1. Import workflows

In the n8n UI: **Workflows → Import from file**, then import each JSON from this folder:

- `Orchestrator Agent.json`
- `Writer Agent.json`
- `Editor Agent.json`
- `Reviewer Agent.json`

Import order does not matter.

### 2. Configure credentials

Create an **OpenAI** credential and attach it to the Chat Model node in each workflow.

For the Orchestrator, also create a **Bearer Auth** credential for the MCP Client node (see step 3).

### 3. Enable MCP

Each sub-agent workflow has **Settings → Available in MCP** enabled so the Orchestrator can call them as tools.

1. In n8n, go to **Settings → MCP** and enable the MCP server.
2. Create an API key / bearer token for MCP access.
3. In **Orchestrator Agent**, open the **MCP Client** node and set:
   - **Endpoint URL:** `http://localhost:5678/mcp-server/http`
   - **Authentication:** Bearer Auth (use the token from step 2)

### 4. Activate workflows

Activate all four workflows. The Orchestrator starts inactive by default — activate it when you are ready to test.

Sub-agent webhooks must be active so MCP can invoke them.

## Run the experiment

1. Open **Orchestrator Agent** in the editor.
2. Use the form trigger (or open the form URL from the **On form submission** node).
3. Enter a briefing, for example:

   > Write a 200-word product announcement for a reusable coffee cup. Tone: friendly, no jargon.

4. Submit and watch the Orchestrator list workflows via MCP, then call Writer → Editor → Reviewer.
5. Inspect execution logs on each workflow to see intermediate outputs.

## Expected behavior

The Orchestrator prompt instructs the agent to:

1. List all workflows through MCP before choosing which to run.
2. Run **Writer → Editor → Reviewer** in a single linear pass.
3. Pass context (briefing, draft, preferences) between steps via MCP tool calls.

The Reviewer returns structured JSON with a `pass` boolean and a `reason` string, so the Orchestrator (or a future iteration) can decide whether to retry or finish.

## Files

```
01_orchestration/
├── README.md                 # this file
├── Orchestrator Agent.json   # form trigger + MCP client + AI agent
├── Writer Agent.json         # webhook + AI agent
├── Editor Agent.json         # webhook + AI agent
└── Reviewer Agent.json       # webhook + information extractor
```

## Notes & limitations

- **Single pass only** — no retry loop if the Reviewer fails; that would be a natural follow-up experiment.
- **MCP on localhost** — the MCP endpoint assumes n8n runs locally on port 5678; adjust the URL if you deploy elsewhere.
- **Credential IDs in exports** — imported JSON may reference credential IDs from the original instance; re-link credentials after import.
- **Model choice** — workflows export with `gpt-5-mini`; change the model in each Chat Model node if needed.

## What to try next

- Add a retry loop when `pass: false`
- Swap the form trigger for a Slack or email trigger
- Replace OpenAI with another provider supported by n8n LangChain nodes
- Measure latency and token cost per agent vs. a single monolithic prompt
