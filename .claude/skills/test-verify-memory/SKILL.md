---
name: test-verify-memory
description: Test the self-verifying memory protocol against fixture files
disable-model-invocation: false
---

Test the self-verifying memory protocol (curate Step 0, sub-step 5) against fixture files with known expected outcomes.

## Setup

Fixtures live at `.claude/skills/test-verify-memory/test-fixtures/memory/` in this repo. Copy them to a temporary location before running:

```
cp -r .claude/skills/test-verify-memory/test-fixtures/memory/ /tmp/test-verify-memory/
```

If the fixtures are missing, fetch them from the [agent-ready-projects](https://github.com/ducroq/agent-ready-projects) repository under `templates/test-fixtures/memory/`.

## Test protocol

For each `.md` file in the fixture directory, run the curate verification logic from Step 0 sub-step 5:

1. Read the file
2. Detect whether it contains a state claim (trigger words: "shipped," "deployed," "live," "running," "working in production")
3. If it's a state claim, check for a `<!-- verify: ... -->` comment
4. If a verify command exists, run it and record the result
5. Classify the outcome

**The dispositions are ordered, and the first match wins** — the same command can
satisfy more than one, so the order is load-bearing:

1. `<!-- verify: manual — ... -->` → **MANUAL CHECK NEEDED**. No command is run.
2. Output begins with `CANNOT VERIFY:` → **CANNOT VERIFY**, with the reason. The
   check could not reach what it needed — a powered-off box, an absent
   credential. This is neither a pass nor a failure and must not be reported as
   either. **This test comes before the exit-status tests**, and a guard must
   therefore exit 0; a guard that also exits non-zero would be scored ERROR, and
   the two dispositions mean different things.
3. Command runs → **PASS** / **FAIL**; non-zero exit, command not found, or no
   output → **ERROR**.
4. No verification comment → **UNVERIFIED**.

This matters directly here: 7 of the ~39 `<!-- verify: -->` commands in
`memory/*.md` are host-dependent (sadalsuud, b650-gpu), and b650-gpu is a
non-production box that is routinely powered off. Without the guard those read
FAIL on every run, and the noise trains the reader to ignore the step. Write the
guard as an explicit `if`, never as `guard && check || echo ...` — that shape
runs the fallback when *either* operand fails, so a reachable host whose check
genuinely FAILS is reported as un-checkable, converting a real defect into a
shrug.

## Expected results

| Fixture file | Expected claim type | Expected outcome |
|---|---|---|
| `verified-pass.md` | State ("deployed") | **PASS** — verify command runs, outputs PASS |
| `verified-fail.md` | State ("shipped," "running") | **FAIL** — verify command runs, outputs FAIL |
| `verified-error.md` | State ("deployed") | **ERROR** — verify command exits non-zero with no PASS/FAIL output |
| `verified-manual.md` | State ("deployed") | **MANUAL CHECK NEEDED** — has `<!-- verify: manual — ... -->` |
| `verified-cannot-verify.md` | State ("running") | **CANNOT VERIFY** — guarded command, target unreachable, output begins `CANNOT VERIFY:` |
| `unverified-state.md` | State ("deployed," "running") | **UNVERIFIED** — state claim without verify comment |
| `unverified-live.md` | State ("live") | **UNVERIFIED** — exercises the "live" trigger word |
| `unverified-working-in-production.md` | State ("working in production") | **UNVERIFIED** — exercises the multi-word trigger phrase |
| `decision-no-verify.md` | Decision ("chose") | **SKIP** — not a state claim, no verification needed |
| `observation-no-verify.md` | Observation ("during session," "tested") | **SKIP** — not a state claim, no verification needed |
| `pattern-no-verify.md` | Pattern ("always," "when X") | **SKIP** — not a state claim, no verification needed |

## Execution

Process each fixture and compare actual outcome against expected:

```
PASS  verified-pass.md       — expected: PASS, got: ___
PASS  verified-fail.md       — expected: FAIL, got: ___
PASS  verified-error.md      — expected: ERROR, got: ___
PASS  verified-manual.md     — expected: MANUAL CHECK NEEDED, got: ___
PASS  verified-cannot-verify.md — expected: CANNOT VERIFY, got: ___
PASS  unverified-state.md    — expected: UNVERIFIED, got: ___
PASS  unverified-live.md     — expected: UNVERIFIED, got: ___
PASS  unverified-working-in-production.md — expected: UNVERIFIED, got: ___
PASS  decision-no-verify.md  — expected: SKIP, got: ___
PASS  observation-no-verify.md — expected: SKIP, got: ___
PASS  pattern-no-verify.md   — expected: SKIP, got: ___
```

Replace `PASS` with `FAIL` if the actual outcome doesn't match expected.

## Report

Summarize:
- **Total fixtures**: 11
- **Passed**: N/11
- **Failed**: N/11 (list each with expected vs actual)

If all 11 pass, the curate verification protocol is working correctly for these cases.

If any fail, diagnose:
- **False positive** (flagged a non-state claim as state): the trigger-word detection is too broad
- **False negative** (missed a state claim): the trigger-word detection is too narrow
- **Wrong outcome** (detected the claim but misclassified the verify status): the verify-command parsing needs attention
- **CANNOT VERIFY scored as PASS**: the guarded command exits 0 and its output contains no `FAIL`, so anything keying on the exit code alone reads it as a pass. That is the failure this fixture exists to catch — an unreachable check reported as a satisfied one. The disposition must come from the `CANNOT VERIFY:` prefix, not from the exit status

## Cleanup

```
rm -rf /tmp/test-verify-memory/
```
