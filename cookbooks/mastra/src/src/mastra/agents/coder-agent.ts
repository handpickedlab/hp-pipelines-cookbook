import { Agent } from '@mastra/core/agent';
import { Memory } from '@mastra/memory';
import { codingWorkspace } from '../workspace/coding-workspace';
import { workerModel } from '../models';

export const coderAgent = new Agent({
  id: 'coder-agent',
  name: 'Coder Agent',
  description:
    'Implements code changes using workspace filesystem tools (read, write, edit, search, execute_command).',
  instructions: `You implement code changes on the active feature branch.

The workspace root IS the repo — use paths like src/app/page.tsx, not blend/src/...

Rules:
- Use search/grep or list_files to find real file paths before read_file — never guess filenames
- Read before you write; prefer edit_file for surgical changes
- Match existing project conventions (package manager, router, component patterns)
- Keep changes minimal and focused on the objective
- Run quick checks with execute_command when helpful (e.g. pnpm run lint on one file)
- End with a summary: files changed, what each change does`,
  model: workerModel,
  workspace: codingWorkspace,
  memory: new Memory(),
  backgroundTasks: { disabled: true },
  defaultOptions: { maxSteps: 30 },
});
