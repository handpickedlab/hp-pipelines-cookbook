import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import { access } from 'node:fs/promises';
import path from 'node:path';
import { runGit } from './git/exec';
import { execInRepo } from './git/run-in-repo';

async function exists(p: string): Promise<boolean> {
  try {
    await access(p);
    return true;
  } catch {
    return false;
  }
}

export async function installDependencies(repoPath: string): Promise<{
  ok: boolean;
  command: string;
  exitCode: number;
  stdout: string;
  stderr: string;
}> {
  const hasPnpmLock = await exists(path.join(repoPath, 'pnpm-lock.yaml'));
  const hasNpmLock = await exists(path.join(repoPath, 'package-lock.json'));
  const hasPackageJson = await exists(path.join(repoPath, 'package.json'));

  if (!hasPackageJson) {
    return {
      ok: true,
      command: '(skip — no package.json)',
      exitCode: 0,
      stdout: 'No Node project detected',
      stderr: '',
    };
  }

  const command = hasPnpmLock
    ? 'CI=true COREPACK_ENABLE_DOWNLOAD_PROMPT=0 pnpm install --frozen-lockfile'
    : hasNpmLock
      ? 'npm ci'
      : 'CI=true COREPACK_ENABLE_DOWNLOAD_PROMPT=0 pnpm install';

  const result = await execInRepo(repoPath, command);
  return {
    ok: result.exitCode === 0,
    command,
    exitCode: result.exitCode,
    stdout: result.stdout,
    stderr: result.stderr,
  };
}

export const installDepsTool = createTool({
  id: 'install-deps',
  description:
    'Install project dependencies in the repo root (pnpm or npm). Required after clone before lint/build.',
  inputSchema: z.object({
    repoPath: z.string().describe('Absolute path to the repository'),
  }),
  execute: async ({ repoPath }) => installDependencies(repoPath),
});
