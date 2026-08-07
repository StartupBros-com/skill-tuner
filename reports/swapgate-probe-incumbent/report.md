# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2268 spent
- verify: 3 trial(s), $0.0650 spent

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/dotfiles/claude/skills-local/writing-for-agents/SKILL.md
- target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- probe calls: 1
- verify calls: 3
- refuted: 1

### Confirmed findings

- **Pruning — single source of truth: duplication (the same meaning in more than one place) costs maintenance and tokens and inflates a meaning's prominence past its real rank.**: This anti-pattern row restates the same rule already stated positively in "Critical rules" ("Include FULL URLs with query params (`?project=xyz`) and open them in Brave."). Likewise the row `Vague "click the button" | Which one? | Click "Create credentials"` restates "Use EXACT element text (copy from the current UI)." The two lists encode the same meanings in two places with no single authoritative source, so a future rule change requires editing both.
  - quote: "| Skip query params | Wrong page loads | Full URL, opened in Brave |"
  - proposed fix: Keep the rule stated once. Either drop the "Skip query params" and "Vague 'click the button'" rows from Anti-patterns (leaving only anti-patterns not already covered by Critical rules, e.g. "Playwright/xvfb for OAuth consent" and "Assume Will knows the IDs"), or drop the corresponding Critical rules bullets and let the Anti-patterns table be the sole source.
- **Steps and completion criteria — Clarity: a vague bound invites premature completion; the criterion should let the agent tell done from not-done.**: The step names the action (re-read the config) but not the success condition — it doesn't state what "verified" means (e.g. the stored value matches the value Will reported). An agent can perform the re-read and consider the step complete without ever checking the result against anything, which is exactly the premature-completion failure the doctrine warns about for vague bounds.
  - quote: "6. Verify (re-read the config via API)"
  - proposed fix: 6. Verify — re-read the config via API and confirm the stored value matches what Will reported.
