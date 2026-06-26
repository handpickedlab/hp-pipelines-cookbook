import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
import { getThreadIdFromContext, resolveRunDir } from '../workspace/paths';
import { writePipelineState } from '../workspace/pipeline-state';
import { runGit } from './git/exec';
import { installDependencies } from './install-deps';

const execFileAsync = promisify(execFile);

function repoDirName(url: string): string {
  const base = url.replace(/\/$/, '').replace(/\.git$/, '');
  return base.split('/').pop() ?? 'repo';
}

export const setupRepoTool = createTool({
  id: 'setup-repo',
  description:
    'One-shot: clone repo, create feature branch, install dependencies, persist active repo for other agents.',
  inputSchema: z.object({
    url: z.string().describe('Git remote URL'),
    branchName: z.string().describe('Feature branch, e.g. feature/add-festival-page'),
    baseBranch: z.string().optional().default('main'),
    directory: z.string().optional().describe('Clone folder name; defaults to repo name from URL'),
  }),
  execute: async ({ url, branchName, baseBranch, directory }, context) => {
    const threadId = getThreadIdFromContext(context?.requestContext);
    const runDir = resolveRunDir(threadId);
    await fs.mkdir(runDir, { recursive: true });

    const dirName = directory ?? repoDirName(url);
    const repoPath = path.join(runDir, dirName);
    await fs.rm(repoPath, { recursive: true, force: true });

    const cloneArgs = ['clone', '--depth', '1', url, repoPath];
    await execFileAsync('git', cloneArgs, { cwd: runDir, maxBuffer: 10 * 1024 * 1024 });

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

    const install = await installDependencies(repoPath);

    await writePipelineState(runDir, {
      repoPath,
      relativePath: dirName,
      branchName,
      repoUrl: url,
    });

    return {
      runDir,
      repoPath,
      relativePath: dirName,
      branchName,
      baseBranch,
      url,
      install,
      message:
        'Repo ready. All agents should use paths relative to repo root (e.g. src/..., not blend/src/...).',
    };
  },
});
