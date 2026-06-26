"""L3 — Orchestrator + revisie-loop + HITL pass.

Volledige casus:
- Writer → Editor → Reviewer in een revisie-loop (max 3 iteraties)
- Na geslaagde review: HITL interrupt voor menselijke approval
- Checkpointing voor resume zonder herstart

Run:  python l3_orchestrator.py
      python l3_orchestrator.py --auto-approve   # sla HITL prompt over (tests)
"""

from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from common import (
    MAX_ITERATIONS,
    BasePipelineState,
    editor_node,
    initial_state,
    reviewer_node,
    ui_payload,
    writer_node,
)
from inputs import BRIEFING, OUTPUT_PREFERENCES

load_dotenv()


class L3State(BasePipelineState, total=False):
    hitl_approved: bool | None
    hitl_feedback: str
    approval_decision: dict | None
    stopped_reason: str


def route_after_review(state: L3State) -> str:
    review = state.get("review")
    if review and review.pass_:
        return "hitl"
    if state.get("iteration", 1) >= MAX_ITERATIONS:
        return "end_max_iterations"
    return "revise"


def prepare_revision(state: L3State) -> dict:
    review = state["review"]
    notes = review.reason if review else "Onbekende reviewfout"
    return {
        "iteration": state.get("iteration", 1) + 1,
        "revision_notes": notes,
    }


def hitl_node(state: L3State) -> dict:
    article = state["article"]
    review = state["review"]
    decision = interrupt(
        {
            "task": "Human approval — keur de finale copy goed of stuur terug met opmerking.",
            "iteration": state.get("iteration", 1),
            "article": article.model_dump(),
            "review": review.model_dump(by_alias=True) if review else None,
        }
    )
    approved = bool(decision.get("approved", False))
    feedback = str(decision.get("feedback", "")).strip()
    return {
        "hitl_approved": approved,
        "hitl_feedback": feedback,
        "approval_decision": {"approved": approved, "feedback": feedback},
        "revision_notes": feedback if not approved else "",
    }


def route_after_hitl(state: L3State) -> str:
    if state.get("hitl_approved"):
        return "end_approved"
    if state.get("iteration", 1) >= MAX_ITERATIONS:
        return "end_max_iterations"
    return "revise_after_hitl"


def prepare_hitl_revision(state: L3State) -> dict:
    feedback = state.get("hitl_feedback", "").strip() or "Menselijke feedback: herzie de copy."
    return {
        "iteration": state.get("iteration", 1) + 1,
        "revision_notes": feedback,
    }


def mark_max_iterations(state: L3State) -> dict:
    return {"stopped_reason": "max_iterations_reached"}


def mark_approved(state: L3State) -> dict:
    return {"stopped_reason": "hitl_approved"}


def build_graph(*, checkpointer=None):
    graph = StateGraph(L3State)
    graph.add_node("writer", writer_node)
    graph.add_node("editor", editor_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("prepare_revision", prepare_revision)
    graph.add_node("prepare_hitl_revision", prepare_hitl_revision)
    graph.add_node("hitl", hitl_node)
    graph.add_node("mark_max_iterations", mark_max_iterations)
    graph.add_node("mark_approved", mark_approved)

    graph.add_edge(START, "writer")
    graph.add_edge("writer", "editor")
    graph.add_edge("editor", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "hitl": "hitl",
            "revise": "prepare_revision",
            "end_max_iterations": "mark_max_iterations",
        },
    )
    graph.add_edge("prepare_revision", "writer")
    graph.add_conditional_edges(
        "hitl",
        route_after_hitl,
        {
            "end_approved": "mark_approved",
            "revise_after_hitl": "prepare_hitl_revision",
            "end_max_iterations": "mark_max_iterations",
        },
    )
    graph.add_edge("prepare_hitl_revision", "writer")
    graph.add_edge("mark_max_iterations", END)
    graph.add_edge("mark_approved", END)

    return graph.compile(checkpointer=checkpointer)


def prompt_hitl_decision() -> dict:
    print("\n--- HITL PASS — menselijke approval ---")
    print("Keur de copy goed (y) of stuur terug met opmerking (n + tekst).")
    answer = input("Goedkeuren? [y/N]: ").strip().lower()
    if answer in {"y", "yes", "ja", "j"}:
        return {"approved": True, "feedback": ""}
    feedback = input("Opmerking voor revisie: ").strip()
    return {"approved": False, "feedback": feedback or "Herzie de copy op basis van menselijke feedback."}


def run(*, auto_approve: bool = False, thread_id: str = "l3-run-1") -> L3State:
    checkpointer = InMemorySaver()
    app = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    result = app.invoke(initial_state(BRIEFING, OUTPUT_PREFERENCES), config)

    while True:
        snapshot = app.get_state(config)
        if not snapshot.next:
            break

        if "hitl" in snapshot.next:
            decision = {"approved": True, "feedback": ""} if auto_approve else prompt_hitl_decision()
            result = app.invoke(Command(resume=decision), config)
            continue

        result = app.invoke(None, config)

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
    print("L3 ORCHESTRATOR — revisie-loop + HITL")
    print("=" * 70)
    print(f"\nIteraties: {payload['iteration_count']} (max {MAX_ITERATIONS})")
    print(f"Gestopt: {payload['stopped_reason']}")
    print(f"HITL: {payload['hitl_approved']}")
    print(f"Reviews: {len(payload['reviews'])}")
    for review in payload["reviews"]:
        status = "PASS" if review["pass"] else "FAIL"
        print(f"  - iter {review['iteration']}: {status} — {review['reason']}")
    print(f"Tussendrafts: {len(payload['drafts'])}")
    print(f"\nTitel: {payload['final_copy']['title']}")
    print(f"Woorden: {payload['final_copy']['word_count']}")
    print(f"must_avoid: {payload['must_avoid_violations'] or 'geen'}")
    print("-" * 70)
    print(payload["final_copy"]["body_markdown"])
    print("-" * 70)
    print("\n--- UI PAYLOAD (JSON) ---")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="L3 orchestrator met HITL")
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Keur automatisch goed na reviewer-pass (handig voor smoke tests)",
    )
    parser.add_argument("--thread-id", default="l3-run-1", help="Checkpoint thread_id")
    args = parser.parse_args(argv)
    run(auto_approve=args.auto_approve, thread_id=args.thread_id)


if __name__ == "__main__":
    main(sys.argv[1:])
