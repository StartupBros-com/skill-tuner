# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.1858 spent
- verify: 12 trial(s), $0.1771 spent

## Run manifest

- run: `dogfood3-browser-console-setup` (2026-08-10T06:30:27Z → 2026-08-10T06:33:15Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/.claude/skills/browser-console-setup/SKILL.md` | `65a8c2e84c7c` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/browser-console-setup/SKILL.md
- probe calls: 1
- verify calls: 12 (3 skeptic(s) per finding)
- refuted: 2

### Confirmed findings

- **Cut identity the body already states [craft]**: This mechanism description in the always-loaded description is restated almost verbatim by the body's 'Core pattern' blockquote ('Open the exact URL in Will's real Windows Brave, hand him precise paste-ready clicks, get the resulting IDs/secrets back, then wire them in programmatically'). The pointer's job is to state when to reach the material, not what it is — the body already carries this identity, so the description pays permanent context load for zero additional routing signal.
  - quote: "by opening the exact URL in the local
  Windows Brave browser and handing paste-ready click steps, then wiring the
  reported credentials into Supabase/Vault/Vercel/.env."
  - proposed fix: Trim the description to routing information only, e.g. 'Set up cloud consoles that block headless automation via a real-browser handoff. Use when a console step cannot be scripted: bot detection, 2FA, CAPTCHA, or OAuth consent screens.' and let the Core Pattern blockquote in the body be the single place the mechanism is spelled out.
- **Duplication / polarity [craft]**: This anti-pattern row restates, negated, the rule the document already gives positively in the Core Pattern blockquote ('do not fight it with Playwright ... Open the exact URL in Will's real Windows Brave') and in 'The problem' section. It is the same meaning written twice under the polarity disguise the doctrine calls out.
  - quote: "| Playwright/xvfb for OAuth consent | Bot detection + cannot do 2FA | Real Brave handoff |"
  - proposed fix: Remove this row from the Anti-patterns table since the Core Pattern and 'The problem' section already establish it positively; keep the table only for guidance not already stated elsewhere (e.g. the 'Assume Will knows the IDs' row).

### Refuted findings

- **One trigger per branch [craft]** — verifier: 'Google OAuth consent' (first parenthetical) and 'OAuth consent screens' (final clause) are the same branch named twice with different wording in the same always-loaded description. A run reaching the skill via either phrase takes the identical path (real-browser handoff, same playbook), so this pays the token cost of routing twice for one branch.
  - quote: "Set up cloud consoles that block headless automation (Google OAuth consent,
  Stripe webhooks, GCP credentials) by opening the exact URL in the local
  Windows Brave browser and handing paste-ready click steps, then wiring the
  reported credentials into Supabase/Vault/Vercel/.env. Use when a console step
  cannot be scripted: bot detection (Google's "browser may not be secure"), 2FA,
  CAPTCHA, or OAuth consent screens."
- **Completion criteria / Demand [craft]** — verifier: "Clear" is a judgment term the agent cannot check without interpretation, unlike the other three checklist items which are binary (rules followed, identifiers included, commands ready). This stray uncheckable qualifier lets the agent tick the box impressionistically rather than verifying the concrete requirement the instruction template already defines ('Report back: [exactly what to copy back, with format]').
  - quote: "- [ ] Clear "report back" format"
