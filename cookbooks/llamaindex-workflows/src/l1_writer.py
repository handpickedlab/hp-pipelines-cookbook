"""L1 — Writer (LlamaIndex Workflow + OpenAI).

De simpelste cel: een Workflow met één step die de Writer draait (structured output).

Run:  python l1_writer.py
"""

from __future__ import annotations

import asyncio

from dotenv import load_dotenv
from llama_index.core.workflow import StartEvent, StopEvent, Workflow, step

from common import apply_update, build_llm_and_counter, initial_state, ui_payload, writer_step
from inputs import BRIEFING, OUTPUT_PREFERENCES

load_dotenv()


class L1Workflow(Workflow):
    @step
    async def write(self, ev: StartEvent) -> StopEvent:
        state = initial_state(ev.get("briefing"), ev.get("preferences"))
        llm, token_counter = build_llm_and_counter()
        apply_update(state, await writer_step(state, llm, token_counter))
        return StopEvent(result=state)


async def _arun(briefing: str, preferences: dict) -> dict:
    workflow = L1Workflow(timeout=300)
    return await workflow.run(briefing=briefing, preferences=preferences)


def generate(briefing: str = BRIEFING, preferences: dict = OUTPUT_PREFERENCES) -> dict:
    return asyncio.run(_arun(briefing, preferences))


def run() -> dict:
    result = generate()
    payload = ui_payload(result, level="L1")
    fc = payload["final_copy"]
    print("=" * 70)
    print("L1 WRITER — OpenAI via LlamaIndex Workflows")
    print("=" * 70)
    print(f"\nTitel: {fc['title']}")
    print(f"Woorden: {fc['word_count']}  {'OK' if fc['within_length_target'] else 'BUITEN MARGE'}\n")
    print("-" * 70)
    print(fc["body_markdown"])
    print("-" * 70)
    print(f"\nmust_avoid overtredingen: {payload['must_avoid_violations'] or 'geen'}")
    print(f"tokens: {payload['totals'].get('tokens_total')} · {payload['totals'].get('duration_ms')} ms")
    return result


if __name__ == "__main__":
    run()
