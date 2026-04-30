#!/usr/bin/env bash
# Build Docker images for Harbor SQL MCP servers.
# Run from the hil_bench/ directory (or any directory).
# Note: ask-human is shared with harbor_swe — build it from harbor_swe/shared/mcp-servers/ask-human/
#
# IMPORTANT: Docker images may be GC'd on this host. Always build images in the
# SAME shell call as harbor run to ensure they remain available.
#
# Canonical run command (matches SWE structure):
#   cd /mnt/efs/tutrinh/src/models/hil_bench   ← must be THIS directory, not hil_bench/hil_bench/
#   bash harbor_sql/build_images.sh && \
#   OPENAI_API_KEY=sk-n2KfL0zcdbzodHgbP9nwpQ \
#   OPENAI_BASE_URL=https://litellm-proxy.ml-serving-internal.scale.com/v1 \
#   harbor run -p harbor_sql/sql_3/<mode> -a terminus-2 -m gpt-4o \
#     --ak max_turns=20 --ak 'api_base=https://litellm-proxy.ml-serving-internal.scale.com/v1' \
#     --no-delete
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$SCRIPT_DIR/shared/mcp-servers"
SWE_ASK_HUMAN_DIR="$SCRIPT_DIR/../harbor_swe/shared/mcp-servers/ask-human"

echo "Building hil-bench-harbor/sql-tools:latest ..."
docker build -t hil-bench-harbor/sql-tools:latest "$MCP_DIR/sql-tools"

echo "Building hil-bench-harbor/business-info:latest ..."
docker build -t hil-bench-harbor/business-info:latest "$MCP_DIR/business-info"

echo "Building hil-bench-harbor/ask-human:latest ..."
docker build -t hil-bench-harbor/ask-human:latest "$SWE_ASK_HUMAN_DIR"

echo ""
echo "All SQL MCP images built:"
docker images | grep "hil-bench-harbor"
