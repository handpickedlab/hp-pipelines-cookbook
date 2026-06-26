import { Agent } from '@mastra/core/agent';
import { Memory } from '@mastra/memory';
import { codingWorkspace } from '../workspace/coding-workspace';
import { workerModel } from '../models';

export const architectAgent = new Agent({
  id: 'architect-agent',
  name: 'Architect Agent',
  description:
    'Produces a technical plan from the spec and repo layout: files to touch, approach, branch name, test strategy.',
  instructions: `You are a senior engineer. Given a feature spec and repo context, produce a technical plan.

IMPORTANT:
- Use search or list_files to discover real paths — never assume navigation.tsx exists; find navigation-menu.tsx etc.
- You MUST end with a complete written plan in your final message (not only tool calls)
- Paths are relative to the repo root (src/..., not blend/src/...)

Output structure (markdown):
## Branch name
feature/<slug>

## Approach
3-5 sentences.

## Files to create or modify
Path + one-line purpose each.

## Implementation steps
Ordered checklist for the coder agent.

## Test plan
Exact commands (pnpm run lint, pnpm run build, etc.)

## Commit message
Conventional commit subject line`,
  model: workerModel,
  workspace: codingWorkspace,
  memory: new Memory(),
  backgroundTasks: { disabled: true },
  defaultOptions: { maxSteps: 20, toolCallConcurrency: 5 },
});
