---
name: feedback-claim-requires-verify
description: Never write "deployed/shipped/uploaded/tested" on intent — a claim is only true once a verify that specifically probes THAT claim has run and its output is captured
metadata:
  type: feedback
---

A status claim (deployed, shipped, uploaded, tested, fixed) is not true until a check
that specifically exercises *that* claim has run and its output is recorded. Writing the
claim from intent — "the commit says deploy, so it deployed" — is the root failure shape
behind the project's most expensive incidents.

**Why:** intent and reality diverge silently. The gap has caused, repeatedly: a "Deploy to
Hub" commit whose upload never ran (#44, 3 days of wrong weights in production); a band-aid
symlink "applied" in a gotcha-log entry that was never created (13h overnight outage); and —
smaller but same shape — commits claiming code was "unit-tested" when no test file was ever
committed (agreement_gate.py, 2026-07-08; and this very memory, referenced 5+ times as
"PROMOTED" but absent as a file until 2026-07-09).

**How to apply — the points this rule has accumulated:**
1. **Never write a deploy/ship/upload word on intent.** Run the action, capture the proof.
   The `.githooks/commit-msg` hook refuses deploy-words on a filter-touching diff whose
   `verify_filter_package.py` check fails — but it can't see memory/gotcha-log prose or reach
   remote hosts, so the discipline of pasting captured output is the only gate for those.
2. **Capture the actual command output** into the commit/memo/gotcha entry — `ls -la`,
   `readlink -f`, `curl … | grep`, `systemctl is-active`, the test run's `N passed`. A claim
   with no captured evidence is an intent, not a fact.
3. **A "shipped/tested" claim about a FILE must point at the committed file.** "Promoted to
   `X.md`" / "unit-tested" is false until `ls X.md` / the test file exists in the tree. Grep
   for the artifact before writing the claim. (Recurred 3×: 6 memories 2026-07-05,
   agreement_gate tests + this memory 2026-07-09.)
4. **Verify gates must probe the specific claim, not adjacent state.** If you can construct a
   world where the verify passes and the claim is false, the verify is wrong-shaped. (A health
   check + a *different* filter's regex passed while the claimed symlink was absent → outage.)
   Corollary (2026-07-04): a verify snippet must probe a *stable* condition (artifact on disk,
   `Result=success`), never a transient runtime port that's only up mid-run.
5. **Remote-infra band-aids are deploys.** `ssh host '…'` that changes production state is a
   deploy claim and needs the same captured-output evidence as a code deploy.

**How to apply — for a new filter specifically:** the training/probe/gate metrics you write
into README/STATUS/commit must come from the actual run's stdout, not from memory of "what it
usually is"; and any "unit-tested" claim for gate/threshold/selection logic requires the test
file committed alongside (mirror `tests/unit/test_agreement_gate.py` /
`tests/unit/test_train_probe.py`). Run the multi-agent review battery BEFORE any paid oracle
run or "verified" claim, not after ([[gotcha-log]] 2026-07-08). See also
[[feedback-multi-agent-review-default]].

<!-- Created 2026-07-09. Referenced as "PROMOTED"/points #4–#5 across memory/gotcha-log.md
(#44, overnight-outage, uplifting-v7 entries) and CLAUDE.md but never actually committed until
now — itself an instance of point #3. Points grounded in those gotcha-log entries. -->
