import { createScorer } from '@mastra/core/evals';

export const taskCompleteScorer = createScorer({
  id: 'coding-task-complete',
  name: 'Coding Task Completeness',
  description: 'Checks whether the supervisor produced a summary and mentioned verification.',
}).generateScore(async context => {
  const text = (context.run.output ?? '').toString();
  if (text.length < 80) return 0;
  const mentionsVerification = /test|build|lint|verify|pass|green|succeed/i.test(text);
  const mentionsChanges = /change|implement|fix|add|update|refactor|commit/i.test(text);
  return mentionsVerification && mentionsChanges ? 1 : 0;
});
