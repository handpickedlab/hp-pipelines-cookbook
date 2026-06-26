import { Agent } from '@mastra/core/agent';
import { Memory } from '@mastra/memory';
import { workerModel } from '../models';

export const plannerAgent = new Agent({
  id: 'planner-agent',
  name: 'Planner Agent',
  description:
    'Turns a feature idea into a structured spec: problem, scope, acceptance criteria, out-of-scope, and risks.',
  instructions: `You are a product-minded planner. Given a feature idea, produce a concise implementation brief.

Output structure (markdown):
## Problem
## Scope
## Out of scope
## Acceptance criteria (numbered, testable)
## Risks & assumptions
## Suggested branch slug (kebab-case, e.g. add-festival-page)

Keep it practical. Do not write code. End with the full written spec in your response.`,
  model: workerModel,
  memory: new Memory(),
  backgroundTasks: { disabled: true },
  defaultOptions: { maxSteps: 5 },
});
