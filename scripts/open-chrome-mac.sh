#!/bin/sh
# Separate local profile. Never point this at your everyday Chrome profile.
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$repo_dir/runs/browser-profile"
exec "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --user-data-dir="$repo_dir/runs/browser-profile" \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9223 \
  --no-first-run --no-default-browser-check \
  https://flow.google.com/
