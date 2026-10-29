#!/usr/bin/env bash
# Builds the derived fixture files: shipit.v2 (status renamed to info) and the T4 data dir.
# Run once from anywhere; writes next to this script. Committed outputs are re-created identically.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
sed -e 's/^STATUS_CMD=status$/STATUS_CMD=info/' \
    -e 's/^  status                Show the active and previous release on each target$/  info                  Show the active and previous release on each target/' \
    "$here/shipit.v1" > "$here/shipit.v2"
grep -q '^STATUS_CMD=info$' "$here/shipit.v2"
grep -q '^  info ' "$here/shipit.v2"
chmod +x "$here/shipit.v1" "$here/shipit.v2"
mkdir -p "$here/data"
python3 -I - "$here/data" <<'EOF'
import os, sys
d = sys.argv[1]
sizes = {"a.bin": 5000, "b.txt": 12000, "c.log": 300, "d.dat": 8000, "e.md": 1200}
for name, n in sizes.items():
    line = "release log line for the shipit fixture\n"
    body = (line * (n // len(line) + 1))[:n]
    with open(os.path.join(d, name), "w") as fh:
        fh.write(body)
    assert os.path.getsize(os.path.join(d, name)) == n, name
print("data ok:", sorted(sizes.items(), key=lambda kv: -kv[1]))
EOF
