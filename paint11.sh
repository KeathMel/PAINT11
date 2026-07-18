#!/bin/bash
# Paint 11 launcher.
# cd's to its own folder, clears stale state, runs the app.

set -e
cd "$(dirname "$(readlink -f "$0")")"

# kill any stale copy of the app still hanging around
pkill -f "python3.*paint11\.py" 2>/dev/null || true

# clear stale bytecode cache
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# pick a python that actually has pygame
PYBIN="python3"
if ! python3 -c "import pygame" 2>/dev/null; then
    if command -v python3.11 >/dev/null 2>&1 && python3.11 -c "import pygame" 2>/dev/null; then
        PYBIN="python3.11"
    fi
fi

exec "$PYBIN" paint11.py "$@"
