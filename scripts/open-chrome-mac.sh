#!/bin/sh
# Separate local profile. Never point this at your everyday Chrome profile.
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_dir"
exec uv run python flow.py open-browser "$@"
