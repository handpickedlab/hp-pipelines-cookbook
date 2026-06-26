import { Agent } from '@mastra/core/agent';
import { Memory } from '@mastra/memory';
import { codingWorkspace } from '../workspace/coding-workspace';
import { setupRepoTool } from '../tools/setup-repo';
import { installDepsTool } from '../tools/install-deps';
import { cloneRepoTool } from '../tools/clone-repo';
import { initRepoTool } from '../tools/init-repo';
import { createFeatureBranchTool } from '../tools/create-feature-branch';
import { workerModel } from '../models';

export const repoAgent = new Agent({
  id: 'repo-agent',
  name: 'Repository Agent',
  description:
    'Sets up repos: prefer setup-repo (clone + branch + install). Reports repoPath and test commands.',
  instructions: `You set up repositories for feature development.

Primary tool: setup-repo — pass url + branchName (feature/<slug>) in one call.

Fallback (only if setup-repo cannot be used):
- clone-repo + create-feature-branch + install-deps

For brand-new local repos without remote: init-repo + create-feature-branch + install-deps

After setup:
- Read package.json scripts and report exact lint/test/build commands
- Report repoPath, branchName, and whether install succeeded

Do not modify application source code.`,
  model: workerModel,
  workspace: codingWorkspace,
  tools: {
    setupRepo: setupRepoTool,
    installDeps: installDepsTool,
    cloneRepo: cloneRepoTool,
    initRepo: initRepoTool,
    createFeatureBranch: createFeatureBranchTool,
  },
  memory: new Memory(),
  backgroundTasks: { disabled: true },
  defaultOptions: { maxSteps: 15 },
});
