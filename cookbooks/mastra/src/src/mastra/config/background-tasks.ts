import type { BackgroundTaskManagerConfig } from '@mastra/core/background-tasks';

/** Global background-task manager — requires LibSQL storage on the Mastra instance. */
export const backgroundTasksConfig: BackgroundTaskManagerConfig = {
  enabled: true,
  globalConcurrency: 10,
  perAgentConcurrency: 5,
  backpressure: 'queue',
  defaultTimeoutMs: 300_000,
  /** Keep the agentic loop open until long subagent / verify runs finish. */
  waitTimeoutMs: 900_000,
};
