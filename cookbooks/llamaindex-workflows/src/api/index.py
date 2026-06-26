"""Vercel serverless web-UI voor de LlamaIndex Workflows writer-benchmark.

Eén FastAPI-app die de pipeline (L1/L2/L3) draait en de `ui_payload` teruggeeft.
Vercel serveert deze ASGI-app (`app`); zie ../vercel.json.

Lokaal (vanuit src/):  uvicorn api.index:app --reload   # http://localhost:8000

L3 draait hier in auto-approve; de echte HITL-pauze (InputRequiredEvent) werkt via de
CLI (`./start.sh l3`). Elke generate() draait de Workflow via asyncio.run.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

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
from common import MAX_ITERATIONS, ui_payload
from inputs import BRIEFING, OUTPUT_PREFERENCES


def run_l1(briefing: str, preferences: dict) -> dict:
    return ui_payload(l1_writer.generate(briefing, preferences), level="L1")


def run_l2(briefing: str, preferences: dict) -> dict:
    result = l2_chain.generate(briefing, preferences)
    review = result.get("review")
    return ui_payload(
        result,
        level="L2",
        extra={
            "review_pass": review.pass_ if review else None,
            "review_reason": review.reason if review else None,
        },
    )


def run_l3(briefing: str, preferences: dict) -> dict:
    result = l3_orchestrator.generate(briefing, preferences, auto_approve=True)
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


def resolve_inputs(req: "RunRequest") -> tuple:
    briefing = (req.briefing or "").strip() or BRIEFING
    prefs = {**OUTPUT_PREFERENCES, **(req.preferences or {})}
    try:
        prefs["length_words"] = int(prefs["length_words"])
    except (TypeError, ValueError, KeyError):
        prefs["length_words"] = OUTPUT_PREFERENCES["length_words"]
    for key in ("must_include", "must_avoid", "structure"):
        if not isinstance(prefs.get(key), list):
            prefs[key] = OUTPUT_PREFERENCES[key]
    return briefing, prefs


app = FastAPI(title="LlamaIndex Workflows writer-benchmark")


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


@app.get("/api/defaults")
def defaults() -> dict:
    return {"briefing": BRIEFING, "preferences": OUTPUT_PREFERENCES}


class RunRequest(BaseModel):
    level: str = "l2"
    briefing: str | None = None
    preferences: dict | None = None


@app.post("/run")
def run(req: RunRequest):
    level = (req.level or "l2").lower()
    if level not in RUNNERS:
        return JSONResponse({"error": f"onbekend niveau '{level}', kies l1|l2|l3"}, status_code=400)
    if not os.environ.get("OPENAI_API_KEY"):
        return JSONResponse(
            {
                "error": "OPENAI_API_KEY ontbreekt op de server. Zet 'm in de Vercel "
                "project settings (Settings → Environment Variables) en redeploy."
            },
            status_code=503,
        )
    briefing, preferences = resolve_inputs(req)
    try:
        return RUNNERS[level](briefing, preferences)
    except Exception as exc:  # noqa: BLE001 — toon de fout netjes in de UI
        return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=500)
