#!/bin/bash
set -euo pipefail

ROOT_DIR="$(dirname "$0")/.."
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to set up the agent. Install it via https://astral.sh/uv/install.sh" >&2
  exit 1
fi

uv sync --extra test
