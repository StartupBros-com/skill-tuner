"""Pull the init and result events out of one run's events.jsonl and log tool use.

Writes into the run root: init.json (model, tools, skills, slash commands, plugins,
MCP servers the arm could see), result.json (the final result event), reply.txt (the
arm's final text), tools.txt (tool_use counts, Skill calls, guidance-skill reads,
fixture-skill edits, fake-CLI calls), status.txt (one line: ok | error <reason>).
Exit 0 only when the status is ok (a failed invocation must not exit 0).
"""
import json
import os
import sys

root, rc = sys.argv[1], sys.argv[2]
events = []
with open(os.path.join(root, "events.jsonl"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            continue

init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), None)
result = next((e for e in reversed(events) if e.get("type") == "result"), None)
keep = ("model", "tools", "skills", "slash_commands", "plugins", "mcp_servers", "cwd",
        "permissionMode", "agents", "output_style", "claude_code_version")
with open(os.path.join(root, "init.json"), "w") as fh:
    json.dump({k: init.get(k) for k in keep} if init else None, fh, indent=1)
with open(os.path.join(root, "result.json"), "w") as fh:
    json.dump(result, fh, indent=1)
with open(os.path.join(root, "reply.txt"), "w") as fh:
    fh.write((result or {}).get("result") or "")

counts, skill_calls, guidance_reads, fixture_edits, cli_calls = {}, [], [], [], []
turns, models = 0, set()
for e in events:
    if e.get("type") != "assistant":
        continue
    msg = e.get("message") or {}
    if msg.get("model"):
        models.add(msg["model"])
    turns += 1
    for block in msg.get("content") or []:
        if not isinstance(block, dict) or block.get("type") != "tool_use":
            continue
        name = block.get("name", "?")
        counts[name] = counts.get(name, 0) + 1
        inp = block.get("input") or {}
        if name == "Skill":
            skill_calls.append(inp.get("skill") or inp.get("command") or str(inp)[:80])
        text = json.dumps(inp)
        if "/cfg/skills/" in text:
            guidance_reads.append((name, text[:160]))
        if "skills/shipit" in text and name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            fixture_edits.append((name, text[:160]))
        if name == "Bash":
            cmd = inp.get("command") or ""
            if "shipit" in cmd:
                cli_calls.append(cmd[:200])

ran_help = any("--help" in c or " -h" in c for c in cli_calls)
with open(os.path.join(root, "tools.txt"), "w") as fh:
    fh.write("assistant_turns=%d\n" % turns)
    fh.write("assistant_models=%s\n" % ",".join(sorted(models)))
    for name in sorted(counts):
        fh.write("%s=%d\n" % (name, counts[name]))
    fh.write("skill_calls=%s\n" % json.dumps(skill_calls))
    fh.write("guidance_reads=%d\n" % len(guidance_reads))
    for name, text in guidance_reads[:40]:
        fh.write("  %s %s\n" % (name, text))
    fh.write("fixture_edits=%d\n" % len(fixture_edits))
    fh.write("cli_calls=%d\n" % len(cli_calls))
    fh.write("ran_help=%s\n" % ("yes" if ran_help else "no"))
    for c in cli_calls[:40]:
        fh.write("  $ %s\n" % c.replace("\n", " "))

if result is None:
    status = "error no-result-event (exit %s)" % rc
elif result.get("is_error"):
    status = "error is_error subtype=%s (exit %s)" % (result.get("subtype"), rc)
else:
    status = "ok subtype=%s turns=%s cost=%s (exit %s)" % (
        result.get("subtype"), result.get("num_turns"), result.get("total_cost_usd"), rc)
with open(os.path.join(root, "status.txt"), "w") as fh:
    fh.write(status + "\n")
print(os.path.basename(root), status)
sys.exit(0 if status.startswith("ok") else 1)
