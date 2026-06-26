import { createScorer } from '@mastra/core/evals';

export const featurePipelineScorer = createScorer({
  id: 'feature-pipeline-complete',
  name: 'Feature Pipeline Completeness',
  description:
    'Checks whether the supervisor delivered a PR handoff with tests and branch info.',
}).generateScore(async context => {
  const text = (context.run.output ?? '').toString().toLowerCase();
  if (text.length < 120) return 0;

  const hasPr =
    text.includes('github.com') ||
    text.includes('pull request') ||
    text.includes('pr url') ||
    text.includes('awaiting-human');
  const hasTests = /test|lint|build|verify|pass|green/.test(text);
  const hasBranch = /feature\//.test(text) || text.includes('branch');

  return hasPr && hasTests && hasBranch ? 1 : 0;
});
