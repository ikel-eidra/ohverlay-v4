# Conflict Resolution Runbook (OHVERLAY)

Use this when merging any branch/PR into `work`.

## 1) Preferred merge model
- Use one controlled maintainer merge path.
- Do **not** click "Accept Incoming" globally.
- For complex files, use "Accept Both" then manually reconcile.

## 2) Must-keep features checklist
After resolving conflicts, verify these survived:

1. `config/settings.py`
   - `ambient.falling_leaves_*`
   - `fish.eye_tracking_damping`
   - private prelaunch app flags
2. `engine/aquarium.py`
   - configurable leaves (`_leaves_enabled`, `_leaf_cycle_seconds`, `_leaf_burst_min/_max`)
   - disable path in `_update_leaves`
3. `ui/skin.py`
   - `_safe_clamped_float`
   - `eye_tracking_damping` clamp
   - `_compute_eye_look` smoothing
4. `main.py`
   - `AquariumSector(..., config=self.config)`
5. Tests
   - `tests/test_config.py` ambient and eye-damping defaults
   - `tests/test_aquarium.py` leaf disable-path coverage

## 3) Post-merge commands (required)
```bash
git status -sb
rg -n "^(<<<<<<<|=======|>>>>>>>)" $(rg --files)
pytest -q
```

## 4) If conflicts are heavy
- Abort merge and retry with a smaller batch of commits.
- Resolve core files first: `settings.py`, `aquarium.py`, `skin.py`, `main.py`, tests.
- Never merge if conflict markers remain.
