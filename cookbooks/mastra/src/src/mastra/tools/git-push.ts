import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import { runGit } from './git/exec';

export const gitPushTool = createTool({
  id: 'git-push',
  description: 'Push the feature branch to origin and set upstream tracking.',
  inputSchema: z.object({
    repoPath: z.string(),
    branchName: z.string(),
    remote: z.string().optional().default('origin'),
  }),
  execute: async ({ repoPath, branchName, remote }) => {
    const { stdout } = await runGit(['push', '-u', remote, branchName], repoPath);
    return { pushed: true, remote, branchName, output: stdout, repoPath };
  },
});
