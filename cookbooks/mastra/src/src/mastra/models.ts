import { createOpenAI } from '@ai-sdk/openai';

/**
 * Explicit OpenAI provider — bypasses models.dev gateway so OPENAI_API_KEY
 * from .env is enough and we avoid "Could not find config for provider openai".
 */
const openai = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

/** Supervisor orchestration (delegation, synthesis). */
export const supervisorModel = openai('gpt-5.5');

/** Subagents: plan, code, verify, release. */
export const workerModel = openai('gpt-5-mini');
