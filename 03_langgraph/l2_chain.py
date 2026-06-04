"""L2 — Writer → Editor → Reviewer (lineair, één pass).

Test wat L2 moet aantonen:
- chaining van drie agent-stappen
- state-passing (tussendrafts zichtbaar)
- UI-ready structured output (JSON payload)

Run:  python l2_chain.py
"""

from __future__ import annotations

import json

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from common import (
    BasePipelineState,
    editor_node,
    initial_state,
    reviewer_node,
    ui_payload,
    writer_node,
)
from inputs import BRIEFING, OUTPUT_PREFERENCES

load_dotenv()


def build_graph():
    graph = StateGraph(BasePipelineState)
    graph.add_node("writer", writer_node)
    graph.add_node("editor", editor_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_edge(START, "writer")
    graph.add_edge("writer", "editor")
    graph.add_edge("editor", "reviewer")
    graph.add_edge("reviewer", END)
    return graph.compile()


def run() -> BasePipelineState:
    app = build_graph()
    result: BasePipelineState = app.invoke(initial_state(BRIEFING, OUTPUT_PREFERENCES))

    payload = ui_payload(
        result,
        level="L2",
        extra={
            "review_pass": result["review"].pass_ if result["review"] else None,
            "review_reason": result["review"].reason if result["review"] else None,
        },
    )

    print("=" * 70)
    print("L2 LINEAIRE CHAIN — Writer → Editor → Reviewer")
    print("=" * 70)
    print(f"\nTitel: {payload['final_copy']['title']}")
    print(
        f"Woorden: {payload['final_copy']['word_count']}  "
        f"({'OK' if payload['final_copy']['within_length_target'] else 'BUITEN MARGE'})"
    )
    print(f"Review: {'PASS' if payload['review_pass'] else 'FAIL'} — {payload['review_reason']}")
    print(f"Tussendrafts: {len(payload['drafts'])}")
    for draft in payload["drafts"]:
        print(f"  - iter {draft['iteration']} / {draft['stage']}: {draft['word_count']} woorden")
    print(f"must_avoid: {payload['must_avoid_violations'] or 'geen'}")
    print("-" * 70)
    print(payload["final_copy"]["body_markdown"])
    print("-" * 70)
    print("\n--- UI PAYLOAD (JSON) ---")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    return result


if __name__ == "__main__":
    run()
