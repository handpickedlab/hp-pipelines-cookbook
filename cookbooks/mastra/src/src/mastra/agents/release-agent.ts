import { Agent } from '@mastra/core/agent';
import { Memory } from '@mastra/memory';
import { codingWorkspace } from '../workspace/coding-workspace';
import { gitCommitTool } from '../tools/git-commit';
import { gitPushTool } from '../tools/git-push';
import { createPullRequestTool } from '../tools/create-pull-request';
import { workerModel } from '../models';

export const releaseAgent = new Agent({
  id: 'release-agent',
  name: 'Release Agent',
  description:
    'Commits verified changes, pushes the feature branch, and opens a GitHub PR for human review. Never merges.',
  instructions: `You ship verified code to GitHub for human review.

Workflow (strict order):
1. Confirm repoPath and feature branch from prior context
2. git status via execute_command in the repo root
3. git-commit with conventional commit message
4. git-push the feature branch
5. create-pull-request — return the PR URL

Rules:
- NEVER merge to main
- If push/PR fails, report GITHUB_TOKEN or gh auth requirements
- PR body: summary, acceptance criteria checklist, test results`,
  model: workerModel,
  workspace: codingWorkspace,
  tools: {
    gitCommit: gitCommitTool,
    gitPush: gitPushTool,
    createPullRequest: createPullRequestTool,
  },
  memory: new Memory(),
  backgroundTasks: { disabled: true },
  defaultOptions: { maxSteps: 12 },
});
