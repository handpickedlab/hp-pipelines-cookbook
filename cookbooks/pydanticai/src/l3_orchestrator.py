"""L3 — Orchestrator + revisie-loop + HITL pass (PydanticAI).

Volledige casus, als plain-Python-orkestratie (PydanticAI heeft geen graph-runtime
nodig voor deze flow):
- Writer → Editor → Reviewer in een revisie-loop (max 3 iteraties)
- Na een geslaagde review: HITL — mens keurt goed of stuurt terug met feedback
- Geen checkpointing/interrupt zoals LangGraph; de loop is gewoon in-memory

Run:  python l3_orchestrator.py
      python l3_orchestrator.py --auto-approve
"""

from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv

from common import (
    MAX_ITERATIONS,
    apply_update,
    editor_step,
    initial_state,
    reviewer_step,
    ui_payload,
    writer_step,
)
from inputs import BRIEFING, OUTPUT_PREFERENCES

load_dotenv()


def generate(
    briefing: str = BRIEFING,
    preferences: dict = OUTPUT_PREFERENCES,
    decide=None,
) -> dict:
    """Draai de loop. `decide` levert na een geslaagde review een
    {"approved": bool, "feedback": str}; None = automatisch goedkeuren (web)."""
    state = initial_state(briefing, preferences)

    while True:
        apply_update(state, writer_step(state))
        apply_update(state, editor_step(state))
        apply_update(state, reviewer_step(state))

        if state["review"].pass_:
            decision = decide() if decide else {"approved": True, "feedback": ""}
            state["hitl_approved"] = bool(decision.get("approved"))
            state["approval_decision"] = decision
            if state["hitl_approved"]:
                state["stopped_reason"] = "hitl_approved"
                return state
            if state["iteration"] >= MAX_ITERATIONS:
                state["stopped_reason"] = "max_iterations_reached"
                return state
            state["iteration"] += 1
            state["revision_notes"] = decision.get("feedback") or "Herzie de copy op basis van menselijke feedback."
            continue

        if state["iteration"] >= MAX_ITERATIONS:
            state["stopped_reason"] = "max_iterations_reached"
            return state
        state["iteration"] += 1
        state["revision_notes"] = state["review"].reason


def prompt_hitl_decision() -> dict:
    print("\n--- HITL PASS — menselijke approval ---")
    answer = input("Goedkeuren? [y/N]: ").strip().lower()
    if answer in {"y", "yes", "ja", "j"}:
        return {"approved": True, "feedback": ""}
    feedback = input("Opmerking voor revisie: ").strip()
    return {"approved": False, "feedback": feedback or "Herzie de copy op basis van menselijke feedback."}


def run(*, auto_approve: bool = False) -> dict:
    result = generate(decide=None if auto_approve else prompt_hitl_decision)
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
    print("L3 ORCHESTRATOR — revisie-loop + HITL (PydanticAI)")
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
    parser = argparse.ArgumentParser(description="L3 orchestrator met HITL (PydanticAI)")
    parser.add_argument("--auto-approve", action="store_true", help="Keur automatisch goed na reviewer-pass")
    args = parser.parse_args(argv)
    run(auto_approve=args.auto_approve)


if __name__ == "__main__":
    main(sys.argv[1:])
