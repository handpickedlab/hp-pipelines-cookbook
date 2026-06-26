import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import { runGit } from './git/exec';

export const gitCommitTool = createTool({
  id: 'git-commit',
  description: 'Stage and commit changes in the repository with a conventional commit message.',
  inputSchema: z.object({
    repoPath: z.string(),
    message: z.string().describe('Conventional commit message, e.g. feat: add health endpoint'),
    paths: z
      .array(z.string())
      .optional()
      .describe('Paths to stage; omit to stage all changes (git add -A)'),
  }),
  execute: async ({ repoPath, message, paths }) => {
    if (paths?.length) {
      await runGit(['add', '--', ...paths], repoPath);
    } else {
      await runGit(['add', '-A'], repoPath);
    }

    const { stdout: status } = await runGit(['status', '--porcelain'], repoPath);
    if (!status) {
      return { committed: false, reason: 'No changes to commit', repoPath };
    }

    const { stdout: commitOut } = await runGit(['commit', '-m', message], repoPath);
    const { stdout: hash } = await runGit(['rev-parse', 'HEAD'], repoPath);

    return {
      committed: true,
      commit: hash,
      message,
      output: commitOut,
      repoPath,
    };
  },
});
