import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

function gitEnv(): NodeJS.ProcessEnv {
  return {
    PATH: process.env.PATH ?? '',
    HOME: process.env.HOME ?? '',
    GIT_TERMINAL_PROMPT: '0',
    ...(process.env.GITHUB_TOKEN
      ? { GH_TOKEN: process.env.GITHUB_TOKEN, GITHUB_TOKEN: process.env.GITHUB_TOKEN }
      : {}),
  };
}

export async function runGit(
  args: string[],
  cwd: string,
): Promise<{ stdout: string; stderr: string }> {
  const { stdout, stderr } = await execFileAsync('git', args, {
    cwd,
    maxBuffer: 10 * 1024 * 1024,
    env: gitEnv(),
  });
  return { stdout: stdout.trim(), stderr: stderr.trim() };
}

export async function runGh(
  args: string[],
  cwd: string,
): Promise<{ stdout: string; stderr: string }> {
  const { stdout, stderr } = await execFileAsync('gh', args, {
    cwd,
    maxBuffer: 10 * 1024 * 1024,
    env: gitEnv(),
  });
  return { stdout: stdout.trim(), stderr: stderr.trim() };
}

export async function currentBranch(repoPath: string): Promise<string> {
  const { stdout } = await runGit(['rev-parse', '--abbrev-ref', 'HEAD'], repoPath);
  return stdout;
}
