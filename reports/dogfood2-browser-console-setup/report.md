# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.1809 spent
- verify: 12 trial(s), $0.1564 spent

## Run manifest

- run: `dogfood2-browser-console-setup` (2026-08-08T10:09:24Z → 2026-08-08T10:11:47Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/.claude/skills/browser-console-setup/SKILL.md` | `65a8c2e84c7c` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/browser-console-setup/SKILL.md
- probe calls: 1
- verify calls: 12 (3 skeptic(s) per finding)
- refuted: 2

### Confirmed findings

- **Cut identity the body already states [craft]**: The description restates, almost clause-for-clause, the mechanism already given in the body's 'Core pattern' blockquote ('Open the exact URL in Will's real Windows Brave, hand him precise paste-ready clicks, get the resulting IDs/secrets back, then wire them in programmatically'). This is identity ('what it is') duplicated in the always-loaded pointer, which should carry only the trigger condition ('when to reach'), not the mechanism the body already explains.
  - quote: "Set up cloud consoles that block headless automation (Google OAuth consent, Stripe webhooks, GCP credentials) by opening the exact URL in the local Windows Brave browser and handing paste-ready click steps, then wiring the reported credentials into Supabase/Vault/Vercel/.env."
  - proposed fix: Trim the description to the trigger condition only, e.g.: 'Use when a console step cannot be scripted: bot detection, 2FA, CAPTCHA, or OAuth consent screens (Google OAuth, Stripe webhooks, GCP credentials).' Let the body's Core pattern block own the explanation of the handoff mechanism.
- **Demand — mixed checkable and uncheckable terms [craft]**: This checklist item's 'Clear' is a subjective, uncheckable qualifier sitting inside an otherwise precise, checkable list (full URLs, exact element text, identifiers included). The doctrine warns that a stray uncheckable qualifier inside a precise list lets the agent satisfy the whole item impressionistically, without a way to tell done from not-done.
  - quote: "- [ ] Clear "report back" format"
  - proposed fix: Replace with the checkable version already stated in the Critical rules section: '- [ ] Report-back format specified exactly (e.g. `GOCSPX-...`, `whsec_...`)'.

### Refuted findings

- **Pruning and drift — polarity duplication [craft]** — verifier: This anti-pattern row is the negated restatement of a rule the document already states positively: the Core pattern block ('do not fight it with Playwright... Open the exact URL in Will's real Windows Brave') and workflow step 2 ('Open the first URL in Brave for Will'). Per the doctrine, an anti-pattern list restating a positively-given rule in negated form is the same meaning written twice.
  - quote: "| Playwright/xvfb for OAuth consent | Bot detection + cannot do 2FA | Real Brave handoff |"
- **Completion criteria [craft]** — verifier: This step names the verification method but not the pass condition, so the agent cannot tell done from not-done without judgment — it can re-read the config and stop there without confirming the value matches what was written. This is the same gap the doctrine's own example calls out: 'Verify the config' is not checkable, but 're-read the config via the API and confirm the field equals the value you wrote' is.
  - quote: "6. Verify (re-read the config via API)"
