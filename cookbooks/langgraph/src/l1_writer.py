"""L1 — Writer (LangGraph + OpenAI).

De simpelste cel uit de matrix: één Writer-node die op basis van de vaste briefing
en output preferences een LinkedIn-artikel schrijft, als structured output.

Run:  python l1_writer.py
"""

from __future__ import annotations

import operator
from typing import Annotated

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from common import (
    Article,
    must_avoid_violations,
    word_count,
    writer_node,
)
from inputs import BRIEFING, OUTPUT_PREFERENCES

load_dotenv()


class WriterState(TypedDict):
    briefing: str
    preferences: dict
    article: Article
    iteration: int
    revision_notes: str
    drafts: Annotated[list, operator.add]
    reviews: Annotated[list, operator.add]
    trace: Annotated[list, operator.add]
    review: None


def build_graph():
    graph = StateGraph(WriterState)
    graph.add_node("writer", writer_node)
    graph.add_edge(START, "writer")
    graph.add_edge("writer", END)
    return graph.compile()


def run() -> WriterState:
    app = build_graph()
    result: WriterState = app.invoke(
        {
            "briefing": BRIEFING,
            "preferences": OUTPUT_PREFERENCES,
            "iteration": 1,
            "revision_notes": "",
            "drafts": [],
            "reviews": [],
            "trace": [],
            "review": None,
        }
    )

    article: Article = result["article"]
    target = OUTPUT_PREFERENCES["length_words"]
    low, high = round(target * 0.9), round(target * 1.1)
    wc = word_count(article.body_markdown)
    within = low <= wc <= high
    violations = must_avoid_violations(article.body_markdown)

    print("=" * 70)
    print("L1 WRITER — OpenAI via LangGraph")
    print("=" * 70)
    print(f"\nTitel: {article.title}")
    print(f"Woorden (geteld): {wc}  (target {target}, marge {low}-{high}) "
          f"{'OK' if within else 'BUITEN MARGE'}\n")
    print("-" * 70)
    print(article.body_markdown)
    print("-" * 70)
    print(f"\nmust_avoid overtredingen: {violations or 'geen'}")

    return result


if __name__ == "__main__":
    run()
