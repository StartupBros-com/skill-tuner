#!/usr/bin/env python3
"""Reconstruct banked-time input content for a run from its manifest.

Every input in a run manifest carries (git_commit, git_path, sha256). This
resolves each target's content via `git show commit:path` in the repo that
owns it, re-hashes, and refuses to emit anything whose sha256 does not match
the manifest — a wrong reconstruction is worse than none.

Writes <out_dir>/<doc-stem>.md plus an index.json mapping absolute
banked paths -> reconstructed relative paths. Stdlib only.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

REPO_FOR_PREFIX = {
    "/home/will/dotfiles/": "/home/will/dotfiles",
}


def owning_repo(path: str) -> str:
    for prefix, repo in REPO_FOR_PREFIX.items():
        if path.startswith(prefix):
            return repo
    raise SystemExit(f"no known repo for {path}")


def git_show(repo: str, commit: str, git_path: str) -> bytes:
    r = subprocess.run(["git", "-C", repo, "show", f"{commit}:{git_path}"],
                       capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"git show failed for {commit}:{git_path}: "
                         f"{r.stderr.decode()[:200]}")
    return r.stdout


def sha(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def recover(inp: dict) -> bytes:
    """Recorded commit first; then the current file (a dirty-at-banking input
    may have been committed since, or never changed); then a history walk."""
    repo = owning_repo(inp["path"])
    content = git_show(repo, inp["git_commit"], inp["git_path"])
    if sha(content) == inp["sha256"]:
        return content
    current = pathlib.Path(inp["path"]).read_bytes()
    if sha(current) == inp["sha256"]:
        return current
    revs = subprocess.run(
        ["git", "-C", repo, "rev-list", "--all", "--", inp["git_path"]],
        capture_output=True, text=True).stdout.split()
    for rev in revs:
        candidate = git_show(repo, rev, inp["git_path"])
        if sha(candidate) == inp["sha256"]:
            return candidate
    raise SystemExit(f"unrecoverable: no source matches {inp['sha256']} "
                     f"for {inp['path']} (dirty={inp.get('dirty')})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, help="reports/<id>/report.json")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    report = json.load(open(args.report))
    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for inp in report["manifest"]["inputs"]:
        if inp["role"] != "target":
            continue
        content = recover(inp)
        stem = pathlib.Path(inp["path"]).parent.name
        dest = out / f"{stem}.md"
        dest.write_bytes(content)
        index[inp["path"]] = dest.name
    (out / "index.json").write_text(json.dumps(index, indent=1) + "\n")
    print(f"reconstructed {len(index)} targets -> {out} (all hashes verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
