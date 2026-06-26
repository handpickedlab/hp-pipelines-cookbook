import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import path from 'node:path';
import { runGit } from './git/exec';
import { getThreadIdFromContext, resolveRunDir } from '../workspace/paths';
import { readPipelineState, writePipelineState } from '../workspace/pipeline-state';

export const createFeatureBranchTool = createTool({
  id: 'create-feature-branch',
  description:
    'Create and checkout a feature branch from a base branch (default main). Run after clone, before coding.',
  inputSchema: z.object({
    repoPath: z.string().describe('Absolute path to the git repository'),
    branchName: z
      .string()
      .describe('Feature branch name, e.g. feature/add-health-endpoint'),
    baseBranch: z.string().optional().default('main'),
  }),
  execute: async ({ repoPath, branchName, baseBranch }, context) => {
    await runGit(['fetch', 'origin', baseBranch], repoPath).catch(() => {});

    try {
      await runGit(['checkout', baseBranch], repoPath);
    } catch {
      try {
        await runGit(['checkout', `origin/${baseBranch}`], repoPath);
      } catch {
        await runGit(['checkout', '-B', baseBranch], repoPath);
      }
    }

    await runGit(['pull', 'origin', baseBranch], repoPath).catch(() => {});
    await runGit(['checkout', '-b', branchName], repoPath);

    const runDir = resolveRunDir(getThreadIdFromContext(context?.requestContext));
    const existing = (await readPipelineState(runDir)) ?? {
      repoPath,
      relativePath: path.basename(repoPath),
    };
    await writePipelineState(runDir, { ...existing, repoPath, branchName });

    return { repoPath, branchName, baseBranch };
  },
});
