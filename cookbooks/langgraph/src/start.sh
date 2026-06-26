#!/bin/bash
set -e
cd "$(dirname "$0")"

LEVEL="${1:-l1}"

if [ ! -d .venv ]; then
  python3 -m venv .venv
  ./.venv/bin/pip install -q -r requirements.txt
fi

case "$LEVEL" in
  l1|L1) SCRIPT=l1_writer.py ;;
  l2|L2) SCRIPT=l2_chain.py ;;
  l3|L3) SCRIPT=l3_orchestrator.py ;;
  *)
    echo "Usage: ./start.sh [l1|l2|l3] [-- extra args voor L3]"
    echo "  l1  Writer alleen (default)"
    echo "  l2  Writer → Editor → Reviewer"
    echo "  l3  Orchestrator + revisie-loop + HITL"
    exit 1
    ;;
esac

shift || true
if [ $# -gt 0 ] && [ "$1" = "--" ]; then
  shift
fi
./.venv/bin/python "$SCRIPT" "$@"
