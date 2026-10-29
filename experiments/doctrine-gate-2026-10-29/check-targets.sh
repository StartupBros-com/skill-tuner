#!/usr/bin/env bash
# check-targets.sh <baseline-run-id> - the pre-leg hard check from predeclare.md.
# Re-hashes every target recorded in the baseline's manifest and exits 1 on any
# mismatch, so a gate leg never pairs fresh counts against a document that
# changed after the baseline was banked (gate.py checks presence, not bytes).
set -u
run="$1"
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
python3 - "$repo/reports/$run/report.json" <<'PY'
import hashlib, json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
bad = 0
for item in report["manifest"]["inputs"]:
    if item.get("role") != "target":
        continue
    path = item["path"]
    recorded = item["sha256"].split(":")[-1]
    try:
        current = hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError as exc:
        print(f"MISSING {path}: {exc}"); bad += 1; continue
    if current != recorded:
        print(f"DRIFTED {path}: recorded {recorded[:12]} now {current[:12]}"); bad += 1
    else:
        print(f"ok      {path}")
print(f"targets checked: drift={bad}")
sys.exit(1 if bad else 0)
PY
