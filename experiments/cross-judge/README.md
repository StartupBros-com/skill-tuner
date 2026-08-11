# Cross-model judge validation

Every scoring run in this repo before 2026-08-11 used a claude-family judge
(claude-sonnet-5) on claude-authored documents. That leaves one standing
objection against the doctrine evidence: a judge that shares a model family
with the generator could share its blind spots, and the v3-vs-ancestor
result could be a family artifact rather than a property of the documents.
This experiment bought a second opinion from a non-Claude frontier model
(codex CLI, profile `auto`, resolved and recorded per call — `gpt-5.6-sol`
on every row) in both directions: precision (are claude's confirmed
findings real by another family's judgment?) and recall (does another
family find defect classes claude missed?).

No claude API dollars were spent; the codex side is subscription-metered.
Wall time ~12 min for 61 adjudications at 6 workers.

## Design: precision (adjudicate.py)

All 61 confirmed findings from the two banked rebank legs
(`rebank-sys-incumbent`, ancestor doctrine, 27 findings;
`rebank-sys-v3`, v3 doctrine, 34) were re-adjudicated blind:

- **Banked-time documents, hash-verified.** The corpus moved after banking
  (the campaign's fixer fleets edited 10 of 15 docs), so `reconstruct.py`
  rebuilds each document from the manifest's `(git_commit, git_path)` and
  refuses any byte stream whose sha256 doesn't match the manifest. One
  dirty-at-banking input recovered via the current-file fallback,
  hash-checked the same way.
- **Blind.** The judge sees document content inline (never a path — the
  fixed current files are on the same disk, and a path would let a
  read-only sandbox unblind itself), the finding's quote, and its issue
  text. It never sees the rule name (doctrine vocabulary identifies the
  leg), the leg, the doctrine, or the fact that three claude skeptics
  already confirmed the finding.
- **Adversarial.** The judge is instructed to refute, mirroring the
  probe's own skeptic gate: `genuine=true` only if the claim survives.

## Result: precision

| leg | cross-judge confirmed | rate |
|---|---|---|
| ancestor (incumbent) | 13/27 | 48% |
| v3 | 16/34 | 47% |

- **Symmetry: Fisher exact two-sided p = 1.000.** The cross-family judge
  applies the same standard to both legs. This is the result of record: if
  v3's advantage were a claude-judging artifact, its findings should
  survive a non-claude audit at a *lower* rate than the ancestor's. They
  survive at the same rate.
- **Paired re-verdict on cross-judge-confirmed findings only:** mean
  +0.200/doc in v3's favor, bootstrap CI [−0.47, +0.87], 7W/4L/4T, sign
  p=0.549 (n=15 docs). Direction preserved; the not_worse posture of the
  replication is unchanged under a different judging family.
- **quote_present 61/61** — no finding was refuted on grounds of a
  fabricated quote. Refutations are substantive disagreements.
- The ~48% absolute survival rate is the honest headline for the
  instrument, not an alarm: this is a second adversarial refute-biased
  filter applied *after* claude's own 3-skeptic gate, and adversarial
  gates are conservative by design (claude's own gate refuted 12/23 raw
  findings in the batch-4 probe). Read it as: about half of
  skeptic-confirmed findings command cross-family consensus; the other
  half are claims a different family argues down — overwhelmingly
  duplication/single-source-of-truth claims where the judge holds that two
  near-repetitions are "not exactly coextensive." That is a real,
  now-documented philosophical difference between the families about what
  counts as duplication, symmetric across legs.

## Design and result: recall (recall_probe.py → overlap.py → claude_adjudicate.py)

Precision can only validate findings claude made; a family blind spot would
live in what claude *missed*. The probe's own prompt (imported from
`probe.py`, not copied) went through the non-claude judge for 5 banked-time
docs — 2 where claude was rich (codex-consult 3 confirmed, automating 5),
3 where claude was sparse (animate, apple-design 1 each; agent-swarm 2).
Then the mirror of Part A: findings that token-overlap nothing in claude's
raw set (confirmed + refuted) were blind-adjudicated by **claude** under
the identical adversarial protocol ($1.94, guarded envelope).

| doc | claude confirmed (capped at 5) | GPT novel | novel endorsed by claude |
|---|---|---|---|
| animate | 1 | 11 | 4 |
| apple-design | 1 | 5 | 1 |
| agent-swarm | 2 | 10 | 3 |
| codex-consult | 3 | 2 | 1 |
| automating-your-automations-local | **5 = the cap** | 10 | **10** |

- **GPT re-found claude's confirmed core.** Of 54 raw GPT findings, 16
  overlap claude's raw set — 12 of them hitting claude-*confirmed*
  findings. Cross-family convergence on what is a defect is strong.
- **The automating row is an instrument finding, not a family finding.**
  The rebank config caps `max_findings` at 5; that doc hit the cap
  exactly, and every one of GPT's 10 uncapped extras was endorsed by
  claude's own judge on review. The cap binds on defect-dense documents
  and silently truncates their yield. (Filed into the playbook: treat an
  at-cap doc as "more remains", not "done".)
- **Ex-cap, no recall blind spot is visible.** Across the other 4 docs the
  novel-and-endorsed yield is 9/4 ≈ 2.3/doc — the same ~2/doc that a
  second *claude* pass yields on already-probed docs (the stopping-rule
  steady state). A single GPT pass behaves like one more independent probe
  pass, not like a detector seeing a class claude cannot.
- **Quote fidelity:** 1 of 54 GPT findings carried a quote not present in
  the document (claude's judge caught it) — the code-level
  `quote_present` guard in the shipped probe exists for exactly this
  failure and is family-agnostic.

## Files

- `reconstruct.py` — manifest-driven, hash-refusing document reconstruction
- `adjudicate.py` — blind adversarial adjudication via codex CLI
- `recall_probe.py` — the probe's own prompt (imported from `probe.py`, not
  copied) through a non-claude judge; inline-doctrine envelope, recorded
  honestly as a different shape from the banked system-prompt legs
- `overlap.py` — novel-vs-refound split (token overlap on target quotes)
- `claude_adjudicate.py` — the mirror direction: claude blind-adjudicates
  GPT's novel findings through the guarded `tune.call_adapter` envelope
- `analyze.py` — confirm rates, Fisher symmetry, paired re-verdict ($0)
- `adjudications.jsonl`, `recall_probe.jsonl`, `novel_findings.json`,
  `claude_adjudications.jsonl` — banked outputs
