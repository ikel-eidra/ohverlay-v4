#!/usr/bin/env bash
set -euo pipefail

echo "[1/5] Branch status"
git status -sb

echo "[2/5] Conflict marker scan"
if rg -n "^(<<<<<<<|=======|>>>>>>>)" $(rg --files); then
  echo "ERROR: Conflict markers found."
  exit 1
else
  echo "OK: no conflict markers found"
fi

echo "[3/5] Required feature markers"
rg -n '"eye_tracking_damping"' config/settings.py ui/skin.py >/dev/null
rg -n '"ambient"|falling_leaves_' config/settings.py >/dev/null
rg -n '_leaves_enabled|_leaf_cycle_seconds|_leaf_burst_min|_leaf_burst_max' engine/aquarium.py >/dev/null
rg -n 'config=self.config' main.py >/dev/null

echo "[4/5] Test sanity"
pytest -q

echo "[5/5] Done: merge audit passed"
