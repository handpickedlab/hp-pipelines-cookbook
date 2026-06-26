import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import { combineVerifyResults, prepareVerification, runScriptCheck } from './verify/lib';

export const verifyProjectTool = createTool({
  id: 'verify-project',
  description:
    'Run install, then lint / test / build in parallel (via verify-project-workflow). Returns structured pass/fail per step.',
  background: {
    enabled: true,
    timeoutMs: 900_000,
    maxRetries: 0,
  },
  inputSchema: z.object({
    repoPath: z.string(),
    skipInstall: z.boolean().optional().default(false),
  }),
  execute: async ({ repoPath, skipInstall }, { mastra }) => {
    const workflow = mastra?.getWorkflow('verifyProjectWorkflow');
    if (workflow) {
      const result = await workflow.start({
        inputData: { repoPath, skipInstall },
      });
      if (result.status === 'success') {
        return result.result;
      }
      return {
        passed: false,
        repoPath,
        steps: [
          {
            name: 'workflow',
            command: 'verify-project-workflow',
            exitCode: 1,
            ok: false,
            stdout: '',
            stderr: result.error?.message ?? 'Workflow failed',
          },
        ],
      };
    }

    // Fallback when workflow is not registered (e.g. isolated tool tests)
    const prepare = await prepareVerification({ repoPath, skipInstall });
    if (prepare.steps.some(s => s.name === 'install' && !s.ok)) {
      return { passed: false, repoPath, steps: prepare.steps };
    }

    const checks = await Promise.all([
      runScriptCheck('lint', prepare),
      runScriptCheck('test', prepare),
      runScriptCheck('build', prepare),
    ]);

    return combineVerifyResults(prepare, checks);
  },
});
