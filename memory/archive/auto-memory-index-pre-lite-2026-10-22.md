*FROZEN 2026-10-22: the user auto-memory index (`~/.claude/projects/-home-jeroen-repos-veen-systems-llm-distillery/memory/MEMORY.md`) verbatim before the framework-lite switch. Its links are relative to THAT directory, not this one. Never edited; not loaded.*

# Memory Index

*One line per entry. Session detail lives in the repo at `memory/project_session_*.md` and `memory/session-log.md` — do not restate it here, and see § Session log below before adding any. This file IS auto-loaded: it is one of two files in the always-loaded layer, budgeted together by `scripts/verification/check_index_budget.py --target loaded` in the llm-distillery repo.*

## How to work here

- ["Investigate" names the method](feedback-investigate-names-the-method.md) — the deliverable stays the noun in the sentence before it; a reply containing only true things is notes, not an answer
- [Plain answers](feedback-plain-answers.md) — answer in one line first, expand every issue number, never reuse a self-coined label as shared vocabulary
- [Decision questions spelled out](feedback-decision-questions-spelled-out.md) — one item per AskUserQuestion, full story, each option says what it MEANS; never bundled/cryptic labels; when the owner is unsure, offer a reversible act-only-where-clear rule
- [Relay marks its gloss](feedback-relay-marks-its-gloss.md) — when relaying an owner decision, mark what was ruled and what is your gloss — a parenthetical beside a ruling inherits its authority and ships as though decided
- [Session close ritual](feedback-session-close-ritual.md) — review battery → cleanup → docs → curate → commit → push-if-applicable → full report + next-session lines
- [Multi-agent review default](feedback-multi-agent-review-default.md) — several review lenses with different framings, not one; blind spots are non-overlapping and it pays most on your own same-day work. ⛔ **VERIFICATION IS NOT REVIEW** — a green battery RAISES the prior that review finds something. Occurrences, the blast-radius and data rungs, and the two-lens case: the file
- [Prose promotion does not fire](feedback-prose-promotion-does-not-fire.md) — ⭐⭐ writing a lesson down does not stop it recurring: SIX promoted patterns recurred in one session, and the decisive one was written in THREE places on the task's own path and missed anyway. Build a check, never a fourth copy
- [Articulating is not applying](feedback-articulating-is-not-applying.md) — ⭐⭐ a fix is the LEAST-reviewed code in any session, and the check is least likely right after you have been most articulate about needing it. Mutation-test in **FIVE** directions (broken, absent, mentioned-but-absent, blast radius, data shapes) — each one's evidence: the file
- [A name is an assertion](feedback-a-name-is-an-assertion.md) — a field, key or TEST name claims what the quantity IS and is read far more often than the note beside it; a surviving mutation is a name that is lying. Both cases: the file
- [A precedent is a mechanism claim](feedback-precedent-is-a-mechanism-claim.md) — "do what we did for X" imports the MECHANISM, not the outcome — the delta fix that rescued one row failed on its twin because the sign was reversed: the file
- [A marker is a claim](feedback-a-marker-is-a-claim.md) — "do not trim / only surviving record / already verified" encodes a premise but reads as an instruction, so nobody probes it — the refuting files were in the marker's OWN directory: the file
- [A decline's reason is local](feedback-decline-reason-is-local.md) — ⛔ **before adopting anything into a fork, grep the DECISIONS file for the feature's own name** — upstream does not know why you declined it, so changelog, skill and code can all agree and still be wrong. Occurrences and the corollary: the file
- [Claim requires verify](feedback-claim-requires-verify.md) — state claims in memory must have verification commands; unverified claims decay
- [The verified artifact is the shipped one](feedback-verified-artifact-is-the-shipped-one.md) — tidying a scratchpad script into a committed module produces a DIFFERENT program, and the tidy-up feels cosmetic so it is never re-run: the file
- [Verify call path](feedback-verify-call-path.md) — verify WHEN a gate's input exists in the flow, not just that the code is right. ⛔ **a PRICE is not a gate — being able to pay it is your code's property, not the vendor's** (a 9-day oracle choice against a rate card with no call site). Occurrence count and the rest: the file
- [Bare issue numbers resolve locally](feedback-bare-issue-number-resolves-locally.md) — `#167` silently resolves to the reader's own repo and reads as correct — qualify EVERY cross-repo appearance, not just the first. ⚠️ ADRs collide too, and that arrives as a confident peer correction: the file
- [Enumeration is not inventory](feedback-enumeration-is-not-inventory.md) — ⭐ state a surface's size from the CODE, never memory — a consumer list inside an issue is a snapshot; grep for who really reads it, and rank by which consumer CHANGES a decision: the file
- [Diff before cross-repo sync](feedback-diff-before-cross-repo-sync.md) — ⛔ **a hand `cp` counts** — `--dry-run` and diff before `deploy_to_nexusmind.sh`; it overwrites, `.nexusmind-owns` is empty, so drift dies silently: the file
- [GitHub push](reference-github-push.md) — pushes work via gh HTTPS token (global insteadOf); SSH keyring agent hangs headless — do NOT re-diagnose the SSH key

## Measurement discipline

- [A sample carries its design weighting](feedback-sample-carries-its-design-weighting.md) — a panel built RIGHT for one question poisons every number derived for another, and nothing in the sample is wrong so review cannot find it. Weights travel as DATA, not as a docstring: the file
- [Hand-built population](feedback-hand-built-population.md) — every measurement error across four repos traced to a population chosen by hand; prefer one the pipeline already computes, and the checker and the checked must be different objects. A stand-in, a denylist and a test fixture are each one — cases: the file
- [Count is not coverage](feedback-count-is-not-coverage.md) — a count of matching rows is not coverage of a failure mode — ask what the LABELLING PROCESS cannot emit. A big reassuring count carries as little as a zero: the file
- [Rate needs population](feedback-rate-needs-population.md) — a pass/screening rate is meaningless without its denominator; test-split and production rates are different quantities, not noisy versions of one
- [A window is part of a source](feedback-window-is-part-of-a-source.md) — if the population's SPAN ≤ the mechanism's PERIOD the zero was guaranteed; print the window beside any retention-bounded count. ⛔ the defect can live in the COMPOSITION, and "recompute a second way" can CONFIRM it — the second way must be one that cannot survive the confusion: the file
- [Noise floor per population](feedback-noise-floor-per-population.md) — ⛔ **a floor belongs to a POPULATION and a MECHANISM, never to a project, and a max-|Δ| check is structurally blind to flips — read the FLIP COUNT at the op-point.** There is no "cross-box" floor (retired 2026-08-29). Every measured term, and the instrument+sampling axis: the file
- [Caveat premise check](feedback-caveat-premise-check.md) — a familiar caveat has a premise, and citing it correctly against the wrong premise retracts good findings — check the conditioning too. Three occurrences: the file
- [Prove the bar is reachable](feedback-prove-the-bar-is-reachable.md) — before DEMANDING a zero, prove a zero is achievable — and read a CONTROL's own firing rate, because a null arm that flags 0 rows cannot catch any. The unreachable bar and the null arm that killed it: the file
- [A dismissal is a claim](feedback-a-dismissal-is-a-claim.md) — an explanation that makes a signal go away must be tested as hard as the signal was — and a dismissal CITING A REAL MEASURED TERM has the citation doing the work of the check. Both occurrences: the file
- [Nothing verifies an estimate](feedback-nothing-verifies-an-estimate.md) — every check here verifies ANSWERS, and decisions turn on ESTIMATES — three cost estimates wrong in one evening, every correction from measuring not arguing: the file
- [Closed accounting is not attribution](feedback-closed-accounting-is-not-attribution.md) — buckets summing to the total is guaranteed by construction — validate each bucket against an INDEPENDENT counter, and check whether an entity can have >1 event: the file
- [Predict the range first](feedback-predict-the-range-first.md) — an implausibly HIGH number is the same instrument signal as a zero and the MORE dangerous half; state the believable range before looking, and a hit inside it is not confirmation if prediction and measurement share a source: the file
- [Check must be specific](feedback-check-must-be-specific.md) — a metric that moves for reasons unrelated to your change cannot confirm it — count the exact quantity, same instrument both sides, plus a presence control. ⛔ when two arms that MUST differ AGREE, that is a result about the instrument. Cases: the file
- [Regex IGNORECASE trap](feedback-regex-ignorecase-trap.md) — a "case-sensitive only" token in a globally-IGNORECASE list isn't; inline `(?-i:)` is decoration if the input was lowercased upstream

## Oracle & modelling

- [Volume is never a target](feedback-volume-is-never-a-target.md) — owner: "volume is never a target, quality is"; success criteria are what must NOT reach readers, never a pass rate
- [Conservative oracle better](feedback-conservative-oracle-better.md) — conservative oracle prompts produce better student models than permissive ones
- [Oracle bias vs noise](feedback-oracle-bias-vs-noise.md) — distinguish systematic bias from random noise; only bias is worth fixing
- [Oracle not ground truth](feedback-oracle-not-ground-truth.md) — oracle scores are labels, not truth; training signal, not evaluation
- [Oracle selection criteria](feedback-oracle-selection-criteria.md) — choosing between oracle providers
- [Probe training data](feedback-probe-training-data.md) — probe training data should match production distribution, not training distribution
- [Scorer always REST](feedback-scorer-always-rest.md) — scorer inference is stateless REST, never stateful sessions

## Infrastructure & landscape

- [sadalsuud pipeline chain](reference-sadalsuud-pipeline-chain.md) — modules are CHAINED: one timer (`fluxus-collection`, every 4h) → `OnSuccess=nexusmind.service`. NexusMind has NO timer and is `inactive` between cycles **by design** — never conclude "no schedule" from that
- [NexusMind data sources](reference-nexusmind-data-sources.md) — `filtered_*.jsonl` ALSO drops source-type-excluded rows; `data/raw/` is pre-enrichment **and is written back into by NexusMind's own preprocessing**, so it is not producer bytes either
- [Cross-repo prioritization](../../../../repos/veen-systems/llm-distillery/memory/cross-repo-prioritization.md) — issue landscape, dependency chains and the cloud-dispatch rules (August rankings archived 2026-09-29); lives in the REPO, not here. ⛔ **It states no board COUNT** — run the `gh` loop at its head and quote with a timestamp; do not restore a count table anywhere
- [Standalone outlets direction](project-standalone-outlets-direction.md) — new lens ideas may target standalone oracle-only outlets, not just ovr.news
- **Never trust `requests`' charset default — hand raw bytes to the parser** (both repos). `requests` returns `ISO-8859-1` for a charset-less `text/*`, so `.decode(resp.encoding or "utf-8")` is dead code. Origin: NexusMind NM#338, the enricher mojibake — CLOSED 2026-08-12, fix verified on production rows in the repo's `memory/corroboration-feature-hypotheses.md`
- [Detector window 128 vs 512](project-detector-128-token-window.md) — TESTED 2026-09-10: 512 is NOT the fix (bands overlap, violence loses recall); the SEED band is 6x larger, and shipped v5 was trained at one seed
- **Harm detector: LIVE, stamp-only since 2026-09-21; nothing gated.** Cap 3,000 → 6,000/run 2026-09-26 (NexusMind#531), **observed 12:11 cycle**: 6000 stamped, files deferred 144 → 140 (one cycle = a direction), stage +4m04s. The unstamped tail is still the OLDEST rows; never quote a corpus-wide rate. ADR-022 SIGNAL amendment ruled (a) (llm-distillery#161). Detail: repo `memory/archive/project_session_2026_09_22_harm_live.md`, `archive/project_session_2026_09_26_v9_live.md`
- [Obituary version ordering is unusable](project-obituary-version-ordering-unusable.md) — v3/v4/v5 recall bands all overlap and the ordering flips across seeds; v4's mean is the HIGHEST, reversing the regression flag. Stop citing the comparison

## Session log

**Not here — the repo carries it (llm-distillery#138, owner 2026-08-29).** This file is auto-loaded and had no rotation rule, no ceiling and no updating step, so its log ran two sessions stale at 9,160 B (47% of the file). ⛔ **Do not restore one** — the auto-loaded copy is the one nobody rotates. Read the repo's `memory/MEMORY.md` (newest four, #123 rotation), `memory/session-log.md` (unbounded record; the removed section is frozen in its appendix) and `memory/project_session_*.md`.
