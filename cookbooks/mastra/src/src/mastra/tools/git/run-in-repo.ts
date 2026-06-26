import { exec } from 'node:child_process';
import { promisify } from 'node:util';

const execAsync = promisify(exec);

export interface RepoExecResult {
  exitCode: number;
  stdout: string;
  stderr: string;
}

export async function execInRepo(
  repoPath: string,
  command: string,
  timeoutMs = 600_000,
): Promise<RepoExecResult> {
  try {
    const { stdout, stderr } = await execAsync(command, {
      cwd: repoPath,
      maxBuffer: 10 * 1024 * 1024,
      timeout: timeoutMs,
      env: {
        ...process.env,
        CI: 'true',
        COREPACK_ENABLE_DOWNLOAD_PROMPT: '0',
        GIT_TERMINAL_PROMPT: '0',
        PATH: process.env.PATH ?? '',
        HOME: process.env.HOME ?? '',
      },
    });
    return { exitCode: 0, stdout: stdout.trim(), stderr: stderr.trim() };
  } catch (error: unknown) {
    const err = error as { code?: number; stdout?: string; stderr?: string; message?: string };
    return {
      exitCode: typeof err.code === 'number' ? err.code : 1,
      stdout: (err.stdout ?? '').toString().trim(),
      stderr: (err.stderr ?? err.message ?? '').toString().trim(),
    };
  }
}
