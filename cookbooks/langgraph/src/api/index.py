"""Vercel serverless web-UI voor de LangGraph writer-benchmark.

Eén FastAPI-app die de pipeline (L1/L2/L3) draait en de `ui_payload` teruggeeft.
Vercel serveert deze ASGI-app (`app`) als serverless function; zie ../vercel.json.

Lokaal draaien (vanuit src/):
    uvicorn api.index:app --reload      # http://localhost:8000

Let op: L3 draait hier in **auto-approve** modus. De echte HITL-pauze (mens keurt
goed/af) werkt alleen via de CLI (`./start.sh l3`), want serverless functions zijn
stateless en houden de `interrupt()`-checkpoint niet vast tussen requests.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Maak de pipeline-modules in src/ (en de UI naast dit bestand) importeerbaar,
# ongeacht vanuit welke directory de function wordt gestart.
HERE = Path(__file__).resolve().parent          # .../src/api
SRC = HERE.parent                                # .../src
for _p in (str(SRC), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dotenv import load_dotenv

load_dotenv(SRC / ".env")  # lokaal; op Vercel komen env vars uit project settings

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import l1_writer
import l2_chain
import l3_orchestrator
from _ui import HTML
from common import MAX_ITERATIONS, initial_state, ui_payload
from inputs import BRIEFING, OUTPUT_PREFERENCES


def run_l1() -> dict:
    graph = l1_writer.build_graph()
    result = graph.invoke(initial_state(BRIEFING, OUTPUT_PREFERENCES))
    return ui_payload(result, level="L1")


def run_l2() -> dict:
    graph = l2_chain.build_graph()
    result = graph.invoke(initial_state(BRIEFING, OUTPUT_PREFERENCES))
    review = result.get("review")
    return ui_payload(
        result,
        level="L2",
        extra={
            "review_pass": review.pass_ if review else None,
            "review_reason": review.reason if review else None,
        },
    )


def run_l3() -> dict:
    """Volledige orchestrator-loop, elke HITL-pauze automatisch goedgekeurd."""
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command

    graph = l3_orchestrator.build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "web-l3"}}
    result = graph.invoke(initial_state(BRIEFING, OUTPUT_PREFERENCES), config)

    while True:
        snapshot = graph.get_state(config)
        if not snapshot.next:
            break
        if "hitl" in snapshot.next:
            result = graph.invoke(Command(resume={"approved": True, "feedback": ""}), config)
        else:
            result = graph.invoke(None, config)

    return ui_payload(
        result,
        level="L3",
        extra={
            "stopped_reason": result.get("stopped_reason"),
            "hitl_approved": result.get("hitl_approved"),
            "approval_decision": result.get("approval_decision"),
            "max_iterations": MAX_ITERATIONS,
            "auto_approved": True,
        },
    )


RUNNERS = {"l1": run_l1, "l2": run_l2, "l3": run_l3}

app = FastAPI(title="LangGraph writer-benchmark")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return HTML


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": os.environ.get("OPENAI_MODEL", "gpt-5.4-mini"),
        "has_key": bool(os.environ.get("OPENAI_API_KEY")),
    }


class RunRequest(BaseModel):
    level: str = "l2"


@app.post("/run")
def run(req: RunRequest):
    level = (req.level or "l2").lower()
    if level not in RUNNERS:
        return JSONResponse(
            {"error": f"onbekend niveau '{level}', kies l1|l2|l3"}, status_code=400
        )
    if not os.environ.get("OPENAI_API_KEY"):
        return JSONResponse(
            {
                "error": "OPENAI_API_KEY ontbreekt op de server. Zet 'm in de Vercel "
                "project settings (Settings → Environment Variables) en redeploy."
            },
            status_code=503,
        )
    try:
        return RUNNERS[level]()
    except Exception as exc:  # noqa: BLE001 — toon de fout netjes in de UI
        return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=500)
