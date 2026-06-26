"""L3 — Orchestrator + revisie-loop + HITL als LlamaIndex Workflow.

Volledige casus, idiomatisch voor Workflows:
- Writer → Editor → Reviewer in een loop; bij fail loopt een event terug naar generate.
- Loop-guard op max 3 iteraties.
- HITL via de ingebouwde InputRequiredEvent/HumanResponseEvent: de Workflow vráágt om
  approval (event op de stream), de runner antwoordt (CLI-prompt of auto-approve).

Run:  python l3_orchestrator.py
      python l3_orchestrator.py --auto-approve
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from dotenv import load_dotenv
from llama_index.core.workflow import (
    Context,
    Event,
    HumanResponseEvent,
    InputRequiredEvent,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

from common import (
    MAX_ITERATIONS,
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


class GenerateEvent(Event):
    state: dict


class ReviewedEvent(Event):
    state: dict


class L3Workflow(Workflow):
    @step
    async def start(self, ev: StartEvent) -> GenerateEvent:
        return GenerateEvent(state=initial_state(ev.get("briefing"), ev.get("preferences")))

    @step
    async def generate(self, ev: GenerateEvent) -> ReviewedEvent:
        state = ev.state
        llm, tc = build_llm_and_counter()
        apply_update(state, await writer_step(state, llm, tc))
        apply_update(state, await editor_step(state, llm, tc))
        apply_update(state, await reviewer_step(state, llm, tc))
        return ReviewedEvent(state=state)

    @step
    async def decide(self, ctx: Context, ev: ReviewedEvent) -> GenerateEvent | StopEvent:
        state = ev.state
        review = state["review"]

        if not review.pass_:
            if state["iteration"] >= MAX_ITERATIONS:
                state["stopped_reason"] = "max_iterations_reached"
                return StopEvent(result=state)
            state["iteration"] += 1
            state["revision_notes"] = review.reason
            return GenerateEvent(state=state)

        # Review geslaagd → HITL: vraag approval en wacht op het antwoord van de runner.
        ctx.write_event_to_stream(InputRequiredEvent(prefix="Goedkeuren? [y/N]: "))
        human = await ctx.wait_for_event(HumanResponseEvent)
        resp = (human.response or "").strip().lower()
        approved = resp in {"y", "yes", "ja", "j"}
        feedback = "" if approved else human.response.strip()

        state["hitl_approved"] = approved
        state["approval_decision"] = {"approved": approved, "feedback": feedback}
        if approved:
            state["stopped_reason"] = "hitl_approved"
            return StopEvent(result=state)
        if state["iteration"] >= MAX_ITERATIONS:
            state["stopped_reason"] = "max_iterations_reached"
            return StopEvent(result=state)
        state["iteration"] += 1
        state["revision_notes"] = feedback or "Herzie de copy op basis van menselijke feedback."
        return GenerateEvent(state=state)


async def _arun(briefing: str, preferences: dict, *, auto_approve: bool, on_input=None) -> dict:
    workflow = L3Workflow(timeout=600)
    handler = workflow.run(briefing=briefing, preferences=preferences)
    async for event in handler.stream_events():
        if isinstance(event, InputRequiredEvent):
            response = "y" if auto_approve else (on_input(event.prefix) if on_input else "y")
            handler.ctx.send_event(HumanResponseEvent(response=response))
    return await handler


def generate(
    briefing: str = BRIEFING,
    preferences: dict = OUTPUT_PREFERENCES,
    *,
    auto_approve: bool = True,
    on_input=None,
) -> dict:
    return asyncio.run(_arun(briefing, preferences, auto_approve=auto_approve, on_input=on_input))


def run(*, auto_approve: bool = False) -> dict:
    result = generate(auto_approve=auto_approve, on_input=None if auto_approve else input)
    payload = ui_payload(
        result,
        level="L3",
        extra={
            "stopped_reason": result.get("stopped_reason"),
            "hitl_approved": result.get("hitl_approved"),
            "approval_decision": result.get("approval_decision"),
            "max_iterations": MAX_ITERATIONS,
        },
    )
    print("=" * 70)
    print("L3 ORCHESTRATOR — revisie-loop + HITL (LlamaIndex Workflows)")
    print("=" * 70)
    print(f"\nIteraties: {payload['iteration_count']} (max {MAX_ITERATIONS})")
    print(f"Gestopt: {payload['stopped_reason']}")
    print(f"HITL: {payload['hitl_approved']}")
    for review in payload["reviews"]:
        print(f"  - iter {review['iteration']}: {'PASS' if review['pass'] else 'FAIL'} — {review['reason']}")
    fc = payload["final_copy"]
    print(f"\nTitel: {fc['title']}")
    print(f"Woorden: {fc['word_count']}")
    print(f"must_avoid: {payload['must_avoid_violations'] or 'geen'}")
    print("-" * 70)
    print(fc["body_markdown"])
    print("-" * 70)
    print("\n--- UI PAYLOAD (JSON) ---")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="L3 orchestrator met HITL (LlamaIndex Workflows)")
    parser.add_argument("--auto-approve", action="store_true", help="Keur automatisch goed na reviewer-pass")
    args = parser.parse_args(argv)
    run(auto_approve=args.auto_approve)


if __name__ == "__main__":
    main(sys.argv[1:])
