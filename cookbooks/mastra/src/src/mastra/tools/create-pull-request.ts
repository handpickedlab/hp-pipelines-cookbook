import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import { currentBranch, runGh } from './git/exec';

export const createPullRequestTool = createTool({
  id: 'create-pull-request',
  description:
    'Open a GitHub pull request via gh CLI. This is the handoff point — a human reviews and merges on GitHub. Never merge automatically.',
  inputSchema: z.object({
    repoPath: z.string(),
    title: z.string(),
    body: z
      .string()
      .describe('PR description: summary, test results, acceptance criteria checklist'),
    base: z.string().optional().default('main'),
    head: z.string().optional().describe('Head branch; defaults to current branch'),
    draft: z.boolean().optional().default(false),
  }),
  execute: async ({ repoPath, title, body, base, head, draft }) => {
    const branch = head ?? (await currentBranch(repoPath));
    const args = [
      'pr',
      'create',
      '--title',
      title,
      '--body',
      body,
      '--base',
      base,
      '--head',
      branch,
    ];
    if (draft) args.push('--draft');

    const { stdout } = await runGh(args, repoPath);
    const prUrl = stdout.match(/https:\/\/github\.com\/\S+/)?.[0] ?? stdout;

    return {
      prUrl,
      title,
      base,
      head: branch,
      status: 'awaiting-human-review',
      message:
        'PR opened. A human must review and merge on GitHub — the agent pipeline stops here.',
    };
  },
});
