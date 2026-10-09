#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
VENV="$ROOT/scratch/.venv-harbor-devin"
HARBOR_COMMIT=dbd6dd045cbd7135c4a3994515df3907e3b9f0ea

command -v uv >/dev/null 2>&1 || {
  echo "uv is required to create the isolated Harbor environment." >&2
  exit 1
}

uv venv --python 3.13 "$VENV"
uv pip install --python "$VENV/bin/python" \
  "harbor @ git+https://github.com/harbor-framework/harbor.git@$HARBOR_COMMIT"

"$VENV/bin/harbor" --version
echo "Installed isolated upstream Harbor at $VENV"
