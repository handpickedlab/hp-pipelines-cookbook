"""L2 — Writer → Editor → Reviewer (lineair, één pass) als LlamaIndex Workflow.

Drie steps geketend via events; de state-dict reist mee in de events.

Run:  python l2_chain.py
"""

from __future__ import annotations

import asyncio
import json

from dotenv import load_dotenv
from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step

from common import (
    apply_update,
    build_llm_and_counter,
    editor_step,
    initial_state,
    reviewer_step,
    ui_payload,
    writer_step,
)
from inputs import BRIEFING, OUTPUT_PREFERENCES

load_dotenv()


class WriteDone(Event):
    state: dict


class EditDone(Event):
    state: dict


class L2Workflow(Workflow):
    @step
    async def write(self, ev: StartEvent) -> WriteDone:
        state = initial_state(ev.get("briefing"), ev.get("preferences"))
        llm, tc = build_llm_and_counter()
        apply_update(state, await writer_step(state, llm, tc))
        return WriteDone(state=state)

    @step
    async def edit(self, ev: WriteDone) -> EditDone:
        llm, tc = build_llm_and_counter()
        apply_update(ev.state, await editor_step(ev.state, llm, tc))
        return EditDone(state=ev.state)

    @step
    async def review(self, ev: EditDone) -> StopEvent:
        llm, tc = build_llm_and_counter()
        apply_update(ev.state, await reviewer_step(ev.state, llm, tc))
        return StopEvent(result=ev.state)


async def _arun(briefing: str, preferences: dict) -> dict:
    workflow = L2Workflow(timeout=300)
    return await workflow.run(briefing=briefing, preferences=preferences)


def generate(briefing: str = BRIEFING, preferences: dict = OUTPUT_PREFERENCES) -> dict:
    return asyncio.run(_arun(briefing, preferences))


def run() -> dict:
    result = generate()
    review = result["review"]
    payload = ui_payload(
        result,
        level="L2",
        extra={
            "review_pass": review.pass_ if review else None,
            "review_reason": review.reason if review else None,
        },
    )
    fc = payload["final_copy"]
    print("=" * 70)
    print("L2 LINEAIRE CHAIN — Writer → Editor → Reviewer (LlamaIndex Workflows)")
    print("=" * 70)
    print(f"\nTitel: {fc['title']}")
    print(f"Woorden: {fc['word_count']}  ({'OK' if fc['within_length_target'] else 'BUITEN MARGE'})")
    print(f"Review: {'PASS' if payload['review_pass'] else 'FAIL'} — {payload['review_reason']}")
    print(f"Tussendrafts: {len(payload['drafts'])}")
    print(f"must_avoid: {payload['must_avoid_violations'] or 'geen'}")
    print("-" * 70)
    print(fc["body_markdown"])
    print("-" * 70)
    print("\n--- UI PAYLOAD (JSON) ---")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    run()
