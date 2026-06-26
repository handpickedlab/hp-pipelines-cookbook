import { Agent } from '@mastra/core/agent';
import { Memory } from '@mastra/memory';
import { repoAgent } from './repo-agent';
import { coderAgent } from './coder-agent';
import { verifierAgent } from './verifier-agent';
import { taskCompleteScorer } from '../scorers/task-complete-scorer';
import { supervisorModel } from '../models';

const codingSupervisorBackgroundTools = {
  repoAgent: false,
  coderAgent: { enabled: true, timeoutMs: 900_000 },
  verifierAgent: { enabled: true, timeoutMs: 900_000 },
} as const;

export const codingSupervisor = new Agent({
  id: 'coding-supervisor',
  name: 'Coding Supervisor',
  instructions: `You autonomously work on code in a sandboxed workspace. You coordinate specialized subagents.

Available subagents:
- repo-agent: Create new local repos (init-repo) or clone remotes (clone-repo), then inspect structure. Use first for any repo setup — including empty new repos with no remote URL.
- coder-agent: Implement code changes (any language/stack). Use after the repo exists.
- verifier-agent: Run install/lint/test/build. Use after coder-agent changes; re-delegate to coder-agent if verification fails.

Delegation strategy:
1. New repo or clone URL or empty workspace → repo-agent
2. Implementation task → coder-agent (pass repo path and constraints from repo-agent)
3. After changes → verifier-agent
4. If verification fails → coder-agent with failure context, then verifier-agent again
5. Stop when verification passes or you cannot progress; summarize what changed

Subagents run as background tasks when long-running — the supervisor keeps coordinating while coder/verifier work. Repo setup stays synchronous. Use streamUntilIdle so task results are merged into the same run.

Success criteria:
- Objective addressed with working, tested code
- Verification commands run and results reported
- Clear summary of files touched and commands that passed`,
  model: supervisorModel,
  agents: {
    repoAgent,
    coderAgent,
    verifierAgent,
  },
  memory: new Memory(),
  backgroundTasks: {
    tools: codingSupervisorBackgroundTools,
    waitTimeoutMs: 900_000,
  },
  defaultOptions: {
    maxSteps: 20,
    delegation: {
      onDelegationStart: async context => {
        if (context.primitiveId === 'coder-agent' && context.iteration > 12) {
          return {
            proceed: false,
            rejectionReason: 'Step budget nearly exhausted — synthesize current state and stop.',
          };
        }
        return { proceed: true };
      },
    },
    isTaskComplete: {
      scorers: [taskCompleteScorer],
      strategy: 'all',
    },
  },
});
