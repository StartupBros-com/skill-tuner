---
name: portfolio
description: Inventory every skill the agent is shown, with its per-turn listing cost, usage count and visibility knob, then decide one skill at a time whether the model should start it on its own. Reads files only; starts on the human's explicit instruction.
argument-hint: "[project directory]"
disable-model-invocation: true
---

Survey the skill portfolio for the project at `$ARGUMENTS`, or the current
directory when that is empty.

`${CLAUDE_PLUGIN_ROOT}` below is Claude Code's expansion for the plugin's
install root. In a client that does not expand it, resolve it yourself: the
plugin root is the directory three levels up from this SKILL.md, the one that
contains `skills/`. `<project-path>` in the command blocks is a slot, not a
variable: replace it with the project directory, keeping the surrounding
double quotes so a path with spaces stays one argument.

## 1. Inventory

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-tuner/scripts/tune.py portfolio --project "<project-path>"
```

It reads skill and command files (Claude Code lists commands beside skills),
settings at user, project and project-local scope, installed plugins and the
usage counters, and makes no model calls. Read the
`report.md` it names. Tell the human three things before the walk: what every
turn pays, the budget line, and every source the report marks missing or
unreadable, including plugin rows marked incomplete. What a turn pays is the
demand when it fits the budget. Over budget, Claude Code shortens descriptions
to bare names until the listing fits, so a turn pays at most the rendered
maximum, and demand is not what the model sees.

Each row is named by its runtime name: the name Claude Code lists, keys
`skillOverrides` on, and counts usage under. A skill whose frontmatter `name`
differs keeps that only as its `display_name`.

## 2. Walk the costliest model-visible skills, one at a time

Take the rows whose tier is `on` or `name-only`, highest listing chars first.
For each, show its row and ask one question first:

**Should the model start this skill on its own?**

- A skill whose effect is the human's own act (signing a document, sending a
  message, publishing in their name), or one they only ever start by typing
  `/name`, is `/`-only by nature. That answer removes its listing cost and
  every misroute at once, so it comes before any wording work.
- When the answer is yes, the next question is whether its description earns
  its characters. The choices are keep it, fix it so it fires on the work the
  human actually does, or name-only. Name-only drops the whole description,
  so it fits only a skill whose name routes on its own and whose description
  carries no exclusion or line against a neighbouring skill; a dropped "not
  for git signing" clause is how a document-signing skill took a GPG request.

Usage counts inform the conversation and never decide it: a skill at zero may
have a description that never matches the human's real work, and fixing the
trigger is as valid an answer as hiding it. Claude Code's usage keys carry no
project, so read a row's usage notes aloud with its count: a key shared with
other projects may include their uses, and uncounted worktree keys are named.
Record the human's answer for each
skill before showing the next. Each skill gets its own answer; a batch
approval covers nothing.

The walk is done when the human has answered for every skill they chose to
look at, or has said to stop.

## 3. Apply what the human chose

Use the knob that actually governs the skill:

- **A skill the human owns** (in their skills folder or this project): set
  `disable-model-invocation: true` in its frontmatter for `/`-only. For a new
  description, run `/skill-tuner:tune <path>`; its step 5 proves routing
  parity before the change lands.
- **Any other non-plugin skill** (claude.ai-synced, bundled, or a managed copy
  the human does not edit): a `skillOverrides` entry in `~/.claude/settings.json`,
  or in the project's `.claude/settings.json` for this project only, keyed by
  the listed name: `"user-invocable-only"` or `"name-only"`.
- **A plugin skill**: Claude Code ignores `skillOverrides` for plugin skills,
  so no per-skill knob exists. Say so. The human's choices are the whole plugin
  off for this project (`"enabledPlugins": {"<plugin>@<marketplace>": false}`
  in the project's `.claude/settings.json`; the plugin table's `saves` column
  estimates what that removes) or a request to the plugin's author.

Settings merge key by key, and the later layer wins: user, then project, then
project-local (`.claude/settings.local.json`). Write each change where it
decides the value. When the report says a local setting decided it (`enabled
by` is `local`, or a tier reason of `override:local`), a change in the project
file loses to it, so make the change in `.claude/settings.local.json`. Copy a
settings file aside before editing it, and change only the keys the human
chose.

## 4. Measure

Re-run step 1. Confirm that each change now shows as the effective state: the
skill's tier and the setting that decided it, or the plugin's enabled value and
its layer. A change that does not show there did not land; say so rather than
counting it. The step is done when you can state what a turn pays before and
after and name each change behind the difference. Over budget, removing
entries lowers demand but can leave what the model sees unchanged until demand
falls under the budget, because other descriptions fill the room. Changes take
effect in the next session, not this one.

## What you may not claim

The inventory counts characters and reads counters. It measures no routing
and no quality, so a smaller listing is the whole measured result: do not
report that the agent now routes or works better. The listing formula and
budget come from one Claude Code release, named in the report; bundled skills
are compiled into Claude Code, are not on disk, and are outside the total.
Over budget, which descriptions survive depends on usage and on an internal
order the inventory cannot see, so the rendered maximum and a plugin's `saves`
are bounds, not measurements. Command subfolders and skills or commands that
only a marketplace entry declares are not inventoried; a plugin row marked
incomplete undercounts.

## Report

- What a turn pays before and after (demand, or the rendered maximum when over
  budget), and the budget line
- Each skill walked: the answer, and what changed
- Skills left as they were, and why
