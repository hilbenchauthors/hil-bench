#!/usr/bin/env bash
set -euo pipefail

cd /app
git apply --verbose /solution/ground_truth.patch
