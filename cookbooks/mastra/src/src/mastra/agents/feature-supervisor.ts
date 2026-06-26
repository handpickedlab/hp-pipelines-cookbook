import { Agent } from '@mastra/core/agent';
import { Memory } from '@mastra/memory';
import { plannerAgent } from './planner-agent';
import { architectAgent } from './architect-agent';
import { repoAgent } from './repo-agent';
import { coderAgent } from './coder-agent';
import { verifierAgent } from './verifier-agent';
import { releaseAgent } from './release-agent';
import { featurePipelineScorer } from '../scorers/feature-pipeline-scorer';
import { supervisorModel } from '../models';

/** Long-running subagent delegations run as background tasks (see streamUntilIdle). */
const supervisorBackgroundTools = {
  architectAgent: { enabled: true, timeoutMs: 600_000 },
  coderAgent: { enabled: true, timeoutMs: 900_000 },
  verifierAgent: { enabled: true, timeoutMs: 900_000 },
  plannerAgent: false,
  repoAgent: false,
  releaseAgent: false,
} as const;

export const featureSupervisor = new Agent({
  id: 'feature-supervisor',
  name: 'Feature Supervisor',
  instructions: `You run an end-to-end feature pipeline from idea to pull request.

## Strict phase order (do not skip or reorder)

### 1. PLAN — planner-agent (once)
User idea + repo URL → written spec with branch slug.

### 2. SETUP — repo-agent (once)
Call setup-repo with git URL + branchName feature/<slug> from the spec.
Wait for repoPath and successful install before continuing.

### 3. DESIGN — architect-agent (once, AFTER setup)
Pass the spec + repoPath. Architect must return a written plan with real file paths.

### 4. BUILD — coder-agent
Pass architect plan + spec. Implement the feature.

### 5. VERIFY — verifier-agent
Call verify-project with repoPath. If it fails, send coder-agent the failure (max 2 fix loops), then verify again.

### 6. SHIP — release-agent (only after VERIFICATION PASSED)
commit → push → create-pull-request. You need the PR URL.

### 7. HANDOFF
Summarize: PR URL, branch, changes, test results, acceptance criteria.
State: "Waiting for human review on GitHub."

## Critical rules
- Never delegate architect before repo setup completes
- Never call release-agent if verification failed
- Never merge to main
- Pass repoPath in every delegation after setup
- Do not re-clone the repo — setup-repo runs once
- Subagents need enough steps — do not pass maxSteps below 10
- Long-running subagents (architect, coder, verifier) run as background tasks — use streamUntilIdle in API clients so results are merged before the run ends`,
  model: supervisorModel,
  agents: {
    plannerAgent,
    architectAgent,
    repoAgent,
    coderAgent,
    verifierAgent,
    releaseAgent,
  },
  memory: new Memory(),
  backgroundTasks: {
    tools: supervisorBackgroundTools,
    waitTimeoutMs: 900_000,
  },
  defaultOptions: {
    maxSteps: 40,
    delegation: {
      onDelegationStart: async context => {
        if (context.iteration > 35) {
          return {
            proceed: false,
            rejectionReason: 'Step budget exhausted — summarize progress and stop.',
          };
        }
        // Studio defaults maxSteps=3 on subagents — override to allow real work
        return { proceed: true, modifiedMaxSteps: 25 };
      },
      messageFilter: ({ messages }) => messages.slice(-20),
    },
    isTaskComplete: {
      scorers: [featurePipelineScorer],
      strategy: 'all',
    },
  },
});
