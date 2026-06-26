import { access, readFile } from 'node:fs/promises';
import path from 'node:path';
import { z } from 'zod';
import { execInRepo } from '../git/run-in-repo';
import { installDependencies } from '../install-deps';

export const verifyStepResultSchema = z.object({
  name: z.string(),
  command: z.string(),
  exitCode: z.number(),
  ok: z.boolean(),
  stdout: z.string(),
  stderr: z.string(),
  skipped: z.boolean().optional(),
});

export type VerifyStepResult = z.infer<typeof verifyStepResultSchema>;

export const verifyWorkflowOutputSchema = z.object({
  passed: z.boolean(),
  repoPath: z.string(),
  steps: z.array(verifyStepResultSchema),
});

export type VerifyWorkflowOutput = z.infer<typeof verifyWorkflowOutputSchema>;

export const verifyPrepareOutputSchema = z.object({
  repoPath: z.string(),
  runPrefix: z.string(),
  scripts: z.object({
    lint: z.boolean(),
    test: z.boolean(),
    build: z.boolean(),
  }),
  steps: z.array(verifyStepResultSchema),
});

export type VerifyPrepareOutput = z.infer<typeof verifyPrepareOutputSchema>;

export async function readPackageScripts(repoPath: string): Promise<Record<string, string>> {
  try {
    const raw = await readFile(path.join(repoPath, 'package.json'), 'utf8');
    const pkg = JSON.parse(raw) as { scripts?: Record<string, string> };
    return pkg.scripts ?? {};
  } catch {
    return {};
  }
}

export async function prepareVerification(input: {
  repoPath: string;
  skipInstall?: boolean;
}): Promise<VerifyPrepareOutput> {
  const { repoPath, skipInstall } = input;
  const steps: VerifyStepResult[] = [];
  const hasPackageJson = await access(path.join(repoPath, 'package.json'))
    .then(() => true)
    .catch(() => false);

  if (hasPackageJson && !skipInstall) {
    const install = await installDependencies(repoPath);
    steps.push({
      name: 'install',
      command: install.command,
      exitCode: install.exitCode,
      ok: install.ok,
      stdout: install.stdout.slice(-4000),
      stderr: install.stderr.slice(-4000),
    });
    if (!install.ok) {
      return {
        repoPath,
        runPrefix: 'pnpm run',
        scripts: { lint: false, test: false, build: false },
        steps,
      };
    }
  }

  const scripts = hasPackageJson ? await readPackageScripts(repoPath) : {};
  const hasPnpmLock = await access(path.join(repoPath, 'pnpm-lock.yaml'))
    .then(() => true)
    .catch(() => false);
  const runPrefix = hasPnpmLock ? 'pnpm run' : 'npm run';

  let hasLint = Boolean(scripts.lint);
  let hasTest = Boolean(scripts.test);
  let hasBuild = Boolean(scripts.build);

  if (!hasLint && !hasTest && !hasBuild && hasPackageJson) {
    hasBuild = true;
  }

  return {
    repoPath,
    runPrefix,
    scripts: { lint: hasLint, test: hasTest, build: hasBuild },
    steps,
  };
}

export async function runScriptCheck(
  name: 'lint' | 'test' | 'build',
  prepare: VerifyPrepareOutput,
): Promise<VerifyStepResult> {
  if (!prepare.scripts[name]) {
    return {
      name,
      command: `(no ${name} script)`,
      exitCode: 0,
      ok: true,
      stdout: 'Skipped — script not defined in package.json',
      stderr: '',
      skipped: true,
    };
  }

  const command = `${prepare.runPrefix} ${name}`;
  const result = await execInRepo(prepare.repoPath, command);
  return {
    name,
    command,
    exitCode: result.exitCode,
    ok: result.exitCode === 0,
    stdout: result.stdout.slice(-4000),
    stderr: result.stderr.slice(-4000),
  };
}

export function combineVerifyResults(
  prepare: VerifyPrepareOutput,
  checks: VerifyStepResult[],
): VerifyWorkflowOutput {
  const steps = [...prepare.steps, ...checks.filter(c => !c.skipped)];
  if (steps.length === 0) {
    steps.push({
      name: 'noop',
      command: '(no package.json scripts)',
      exitCode: 0,
      ok: true,
      stdout: 'No automated checks configured',
      stderr: '',
      skipped: true,
    });
  }

  const installFailed = prepare.steps.some(s => s.name === 'install' && !s.ok);
  const passed = !installFailed && checks.every(c => c.ok);

  return { passed, repoPath: prepare.repoPath, steps };
}
