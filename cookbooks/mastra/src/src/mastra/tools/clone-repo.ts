import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
import { getThreadIdFromContext, resolveRunDir } from '../workspace/paths';
import { writePipelineState } from '../workspace/pipeline-state';

const execFileAsync = promisify(execFile);

function repoDirName(url: string): string {
  const base = url.replace(/\/$/, '').replace(/\.git$/, '');
  return base.split('/').pop() ?? 'repo';
}

export const cloneRepoTool = createTool({
  id: 'clone-repo',
  description:
    'Clone a git repository into the current workspace run directory. Returns the path to work in.',
  inputSchema: z.object({
    url: z.string().describe('Git remote URL (https or ssh)'),
    branch: z.string().optional().describe('Branch to checkout'),
    directory: z.string().optional().describe('Target folder name under the run root'),
  }),
  execute: async ({ url, branch, directory }, context) => {
    const threadId = getThreadIdFromContext(context?.requestContext);
    const runDir = resolveRunDir(threadId);
    await fs.mkdir(runDir, { recursive: true });

    const dirName = directory ?? repoDirName(url);
    const targetPath = path.join(runDir, dirName);
    await fs.rm(targetPath, { recursive: true, force: true });

    const args = ['clone', '--depth', '1'];
    if (branch) args.push('--branch', branch);
    args.push(url, targetPath);

    await execFileAsync('git', args, { cwd: runDir, maxBuffer: 10 * 1024 * 1024 });

    let currentBranch = branch;
    if (!currentBranch) {
      const { stdout } = await execFileAsync('git', ['rev-parse', '--abbrev-ref', 'HEAD'], {
        cwd: targetPath,
      });
      currentBranch = stdout.trim();
    }

    await writePipelineState(runDir, {
      repoPath: targetPath,
      relativePath: dirName,
      repoUrl: url,
    });

    return {
      runDir,
      repoPath: targetPath,
      relativePath: dirName,
      branch: currentBranch,
      url,
    };
  },
});
