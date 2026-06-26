import { createStep, createWorkflow } from '@mastra/core/workflows';
import { z } from 'zod';
import {
  combineVerifyResults,
  prepareVerification,
  runScriptCheck,
  verifyPrepareOutputSchema,
  verifyStepResultSchema,
  verifyWorkflowOutputSchema,
} from '../tools/verify/lib';

const workflowInputSchema = z.object({
  repoPath: z.string(),
  skipInstall: z.boolean().optional().default(false),
});

const workflowStateSchema = z.object({
  prepare: verifyPrepareOutputSchema.optional(),
});

const prepareStep = createStep({
  id: 'prepare',
  description: 'Install dependencies and discover lint/test/build scripts',
  inputSchema: workflowInputSchema,
  outputSchema: verifyPrepareOutputSchema,
  execute: async ({ inputData, setState, state }) => {
    const prepare = await prepareVerification(inputData);
    await setState({ ...state, prepare });
    return prepare;
  },
});

const lintStep = createStep({
  id: 'lint',
  description: 'Run lint in parallel with test and build',
  inputSchema: verifyPrepareOutputSchema,
  outputSchema: verifyStepResultSchema,
  execute: async ({ inputData }) => runScriptCheck('lint', inputData),
});

const testStep = createStep({
  id: 'test',
  description: 'Run tests in parallel with lint and build',
  inputSchema: verifyPrepareOutputSchema,
  outputSchema: verifyStepResultSchema,
  execute: async ({ inputData }) => runScriptCheck('test', inputData),
});

const buildStep = createStep({
  id: 'build',
  description: 'Run build in parallel with lint and test',
  inputSchema: verifyPrepareOutputSchema,
  outputSchema: verifyStepResultSchema,
  execute: async ({ inputData }) => runScriptCheck('build', inputData),
});

const combineStep = createStep({
  id: 'combine',
  description: 'Aggregate parallel check results into a single pass/fail report',
  inputSchema: z.object({
    lint: verifyStepResultSchema,
    test: verifyStepResultSchema,
    build: verifyStepResultSchema,
  }),
  outputSchema: verifyWorkflowOutputSchema,
  execute: async ({ inputData, state }) => {
    const prepare = state.prepare;
    if (!prepare) {
      throw new Error('Workflow state missing prepare output');
    }
    return combineVerifyResults(prepare, [inputData.lint, inputData.test, inputData.build]);
  },
});

export const verifyProjectWorkflow = createWorkflow({
  id: 'verify-project-workflow',
  description: 'Install once, then run lint / test / build in parallel',
  inputSchema: workflowInputSchema,
  outputSchema: verifyWorkflowOutputSchema,
  stateSchema: workflowStateSchema,
})
  .then(prepareStep)
  .parallel([lintStep, testStep, buildStep])
  .then(combineStep)
  .commit();
