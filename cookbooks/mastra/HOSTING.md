# HOSTING — Mastra (feature pipeline)

End-to-end feature delivery: idee → spec → design → branch → code → test → commit → push → PR → **mens reviewt en merge't op GitHub**.

## Pipeline

```
feature-supervisor
├── planner-agent    → spec + acceptance criteria
├── architect-agent  → technisch plan + branch naam
├── repo-agent       → clone + feature branch + inspectie
├── coder-agent      → implementatie (code mode + sandbox)
├── verifier-agent   → lint / test / build
└── release-agent    → commit → push → PR openen
                              ↓
                    👤 mens reviewt PR op GitHub
```

Start in Studio met agent **feature-supervisor** (niet coding-supervisor — die is voor losse coding-taken zonder PR-flow).

## Lokaal draaien

```bash
cd src
cp .env.example .env
pnpm install
pnpm run dev
```

### Vereisten

| Tool | Waarom |
|---|---|
| `git` | Clone, branch, commit |
| `gh` | PR aanmaken (`brew install gh`) |
| `GITHUB_TOKEN` of `gh auth login` | Push + PR naar GitHub |

### Voorbeeldprompt

> Feature: add a GET /health endpoint that returns `{ "status": "ok" }`.
> Repo: https://github.com/your-org/your-repo.git

De supervisor vraagt om de repo-URL als die ontbreekt.

## Concurrency

Twee lagen voor snellere runs:

### Agent-level background tasks

- Ingeschakeld op de Mastra-instance (`backgroundTasks` + LibSQL storage).
- **feature-supervisor** / **coding-supervisor** draaien lange subagent-delegaties (architect, coder, verifier) als background tasks.
- Plan → setup → ship blijven **synchroon** (repo-agent, planner, release).
- Subagents hebben `backgroundTasks: { disabled: true }` zodat hun eigen tools niet dubbel async worden.

**Studio:** gebruik een memory thread en `streamUntilIdle()` — niet plain `stream()` — zodat background-task resultaten in dezelfde run worden verwerkt. Zie [background tasks](https://mastra.ai/docs/agents/background-tasks) en [streamUntilIdle](https://mastra.ai/reference/streaming/agents/streamUntilIdle).

### Workflow-level parallelism

- Workflow **`verify-project-workflow`**: `prepare` (install) → `.parallel([lint, test, build])` → `combine`.
- Het `verify-project` tool roept deze workflow aan; lint/test/build lopen tegelijk na install.

## Env vars

| Variabele | Verplicht | Opmerking |
|---|---|---|
| `OPENAI_API_KEY` | Ja | Alle agents |
| `GITHUB_TOKEN` | Ja voor ship-fase | `repo` scope; of `gh auth login` |

## Human gate

De pipeline **stopt na PR-aanmaak**. Er is geen auto-merge — dat is bewust:

1. `release-agent` opent de PR via `gh pr create`
2. Jij reviewt op GitHub (CI, diff, acceptance criteria)
3. Jij merge't naar `main` als het goed is

## Agents

| Agent | Entry point? | Doel |
|---|---|---|
| `feature-supervisor` | **Ja** | Volledige feature pipeline |
| `coding-supervisor` | Nee | Losse sandbox-taken zonder git/PR |

## Projectstructuur

```
src/mastra/
├── agents/
│   ├── feature-supervisor.ts   ← start hier
│   ├── planner-agent.ts
│   ├── architect-agent.ts
│   ├── repo-agent.ts
│   ├── coder-agent.ts
│   ├── verifier-agent.ts
│   └── release-agent.ts
├── tools/
│   ├── setup-repo.ts
│   ├── verify-project.ts
│   ├── verify/lib.ts
│   └── install-deps.ts
├── workflows/
│   └── verify-project-workflow.ts
└── workspace/
```

## Live zetten (Vercel)

Niet aanbevolen voor deze pipeline — `LocalSandbox` + `git` + `gh` vereisen een echte machine. Draai lokaal of op een VM met git/gh credentials.
