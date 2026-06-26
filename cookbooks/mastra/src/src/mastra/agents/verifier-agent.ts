import { Agent } from '@mastra/core/agent';
import { Memory } from '@mastra/memory';
import { codingWorkspace } from '../workspace/coding-workspace';
import { verifyProjectTool } from '../tools/verify-project';
import { workerModel } from '../models';

export const verifierAgent = new Agent({
  id: 'verifier-agent',
  name: 'Verifier Agent',
  description:
    'Runs verify-project (install + lint + build) and reports structured pass/fail. Does not improvise dozens of shell commands.',
  instructions: `You verify code changes.

Primary tool: verify-project with the repoPath from setup (runs install, then lint/test/build in parallel via workflow).

If verify-project fails:
- Report which step failed (install, lint, build) with stderr
- Suggest the smallest fix for the coder agent
- Do NOT run ad-hoc install/lint loops — one verify-project call per attempt is enough

If all steps pass, state clearly: VERIFICATION PASSED`,
  model: workerModel,
  workspace: codingWorkspace,
  tools: { verifyProject: verifyProjectTool },
  memory: new Memory(),
  backgroundTasks: { disabled: true },
  defaultOptions: { maxSteps: 8 },
});
