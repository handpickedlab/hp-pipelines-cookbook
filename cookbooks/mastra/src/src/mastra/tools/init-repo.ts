import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
import { getThreadIdFromContext, resolveRunDir } from '../workspace/paths';
import { writePipelineState } from '../workspace/pipeline-state';

const execFileAsync = promisify(execFile);

export const initRepoTool = createTool({
  id: 'init-repo',
  description:
    'Create a new empty project directory in the workspace. Optionally writes README.md and runs git init.',
  inputSchema: z.object({
    name: z
      .string()
      .describe('Directory name for the new repo (e.g. test-repo)'),
    readme: z
      .string()
      .optional()
      .describe('README.md contents; pass empty string for an empty file'),
    gitInit: z.boolean().optional().default(true),
  }),
  execute: async ({ name, readme, gitInit = true }, context) => {
    const threadId = getThreadIdFromContext(context?.requestContext);
    const runDir = resolveRunDir(threadId);
    const repoPath = path.join(runDir, name);

    await fs.mkdir(repoPath, { recursive: true });

    if (readme !== undefined) {
      await fs.writeFile(path.join(repoPath, 'README.md'), readme, 'utf8');
    }

    if (gitInit) {
      await execFileAsync('git', ['init'], { cwd: repoPath });
    }

    await writePipelineState(runDir, { repoPath, relativePath: name });

    return {
      runDir,
      repoPath,
      relativePath: name,
      gitInitialized: gitInit,
      hasReadme: readme !== undefined,
    };
  },
});
