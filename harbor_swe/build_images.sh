#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building Harbor SWE MCP server images from packaged contexts..."
"$SCRIPT_DIR/warmup_images.sh" --build-local-sidecars
echo "Done."
