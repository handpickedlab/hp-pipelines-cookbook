
import { Mastra } from '@mastra/core/mastra';
import { VercelDeployer } from '@mastra/deployer-vercel';
import { PinoLogger } from '@mastra/loggers';
import { LibSQLStore } from '@mastra/libsql';
import { DuckDBStore } from '@mastra/duckdb';
import { MastraCompositeStore } from '@mastra/core/storage';
import {
  Observability,
  MastraStorageExporter,
  MastraPlatformExporter,
  SensitiveDataFilter,
} from '@mastra/observability';
import { featureSupervisor } from './agents/feature-supervisor';
import { codingSupervisor } from './agents/coding-supervisor';
import { plannerAgent } from './agents/planner-agent';
import { architectAgent } from './agents/architect-agent';
import { repoAgent } from './agents/repo-agent';
import { coderAgent } from './agents/coder-agent';
import { verifierAgent } from './agents/verifier-agent';
import { releaseAgent } from './agents/release-agent';
import { featurePipelineScorer } from './scorers/feature-pipeline-scorer';
import { taskCompleteScorer } from './scorers/task-complete-scorer';
import { backgroundTasksConfig } from './config/background-tasks';
import { verifyProjectWorkflow } from './workflows/verify-project-workflow';

export const mastra = new Mastra({
  deployer: new VercelDeployer({ studio: true }),
  agents: {
    featureSupervisor,
    codingSupervisor,
    plannerAgent,
    architectAgent,
    repoAgent,
    coderAgent,
    verifierAgent,
    releaseAgent,
  },
  scorers: { featurePipelineScorer, taskCompleteScorer },
  workflows: {
    verifyProjectWorkflow,
  },
  backgroundTasks: backgroundTasksConfig,
  storage: new MastraCompositeStore({
    id: 'composite-storage',
    default: new LibSQLStore({
      id: 'mastra-storage',
      url: 'file:./mastra.db',
    }),
    domains: {
      observability: await new DuckDBStore().getStore('observability'),
    },
  }),
  logger: new PinoLogger({
    name: 'Mastra',
    level: 'info',
  }),
  observability: new Observability({
    configs: {
      default: {
        serviceName: 'mastra',
        exporters: [
          new MastraStorageExporter(),
          new MastraPlatformExporter(),
        ],
        spanOutputProcessors: [new SensitiveDataFilter()],
      },
    },
  }),
});
