#!/bin/sh
set -eu

RUN_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$RUN_DIR/../.." && pwd)
HARBOR="$ROOT/scratch/.venv-harbor-devin/bin/harbor"
PYTHON="$ROOT/scratch/.venv-harbor-devin/bin/python"
JOB_DIR="$ROOT/scratch/devin-swe-2-max-ask-human/hil-bench-devin-swe-2-max-ask-human"

if [ ! -x "$HARBOR" ]; then
  echo "Missing isolated Harbor environment. Run $RUN_DIR/setup.sh first." >&2
  exit 1
fi
if [ ! -f "$ROOT/.env" ]; then
  echo "Missing $ROOT/.env with the required credentials." >&2
  exit 1
fi

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export ASK_HUMAN_BACKEND=litellm_proxy
export ASK_HUMAN_MODEL=gpt-4.1-mini

cd "$ROOT"
"$HARBOR" run \
  --config "$RUN_DIR/config.yaml" \
  --env-file "$ROOT/.env" \
  "$@"

"$PYTHON" "$RUN_DIR/summarize_pass3.py" "$JOB_DIR"
