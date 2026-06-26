"""L2 — Writer → Editor → Reviewer (lineair, één pass).

Drie PydanticAI-agents na elkaar; print een UI-ready JSON-payload.

Run:  python l2_chain.py
"""

from __future__ import annotations

import json

from dotenv import load_dotenv

from common import (
    apply_update,
    editor_step,
    initial_state,
    reviewer_step,
    ui_payload,
    writer_step,
)
from inputs import BRIEFING, OUTPUT_PREFERENCES

load_dotenv()


def generate(briefing: str = BRIEFING, preferences: dict = OUTPUT_PREFERENCES) -> dict:
    state = initial_state(briefing, preferences)
    apply_update(state, writer_step(state))
    apply_update(state, editor_step(state))
    apply_update(state, reviewer_step(state))
    return state


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
    print("L2 LINEAIRE CHAIN — Writer → Editor → Reviewer (PydanticAI)")
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
