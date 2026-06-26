"""L1 — Writer (PydanticAI + OpenAI).

De simpelste cel: één Writer-agent met structured output (output_type=Article).

Run:  python l1_writer.py
"""

from __future__ import annotations

from dotenv import load_dotenv

from common import apply_update, initial_state, ui_payload, writer_step
from inputs import BRIEFING, OUTPUT_PREFERENCES

load_dotenv()


def generate(briefing: str = BRIEFING, preferences: dict = OUTPUT_PREFERENCES) -> dict:
    state = initial_state(briefing, preferences)
    apply_update(state, writer_step(state))
    return state


def run() -> dict:
    result = generate()
    payload = ui_payload(result, level="L1")
    fc = payload["final_copy"]
    print("=" * 70)
    print("L1 WRITER — OpenAI via PydanticAI")
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
