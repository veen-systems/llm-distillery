---
name: project_session_2026_08_07_evening
description: Chain re-verification found two ✅-but-open links; built and deployed pipeline-atlas (6th repo); a six-lens review battery found 15 false claims in a site whose only job is being true
metadata:
  type: project
---

# 2026-08-07 evening — the atlas, and the review that gutted it

## One line

Re-queried every chain link against GitHub and found **two marked ✅ while
open**; built **`veen-systems/pipeline-atlas`**, a whole-chain architecture site
plus a live ops snapshot, deployed on sadalsuud over Tailscale; then a six-lens
review battery found **15 outright false claims in it, a crash, and an RCE path**
— all fixed.

## Part 1 — chain verification

Every issue named in Chains 1–15 fetched with `gh issue view` rather than read
off the board. Board was broadly right; **the diagrams were not.**

| Link | Marked | Actual |
|---|---|---|
| **LD#73** (Chain 2 head) | ✅ | OPEN — but genuinely done, shipped as `violence_promotion v1`. **Closed.** |
| **NM#185** (Chain 1) | ✅ | OPEN, and **not** bookkeeping. |

**NM#185 is the finding.** It bundles the obituary blocker (shipped, enforcing)
with a **commerce prefilter v3 retrain that was never started** —
`filters/common/commerce_prefilter/` holds v1 and v2 only, and v1 is
force-pinned (LD#80) because v2 underperformed. The finished half made the
whole issue look done, so Chain 1 read "COMPLETE except one cosmetic link".

**And its evidence has decayed:** NM#185's commerce miss set was **100%
`sustainability_technology`**, a filter deleted 2026-08-03. Before any v3
training run, re-measure against `solutions v6`. Recorded as an open hypothesis
in `docs/TODO.md` — settling it costs one count, not a retrain.

Also: **ovr#204 is not blocked** despite its title ("after NexusMind#185
ships") — the half it depends on shipped five weeks ago.

**Coverage hole:** persuasion-scorer's 12 issues were counted in every total on
the board and banded nowhere. Now **Chain 16**. ps#4 is a spend gate, ps#2 a
phase gate.

Closed: LD#73, LD#97, NM#204. Commented: NM#185, ovr#204.

## Part 2 — pipeline-atlas (new, sixth repo)

**Why:** eight partial architecture documents across four repos, no whole-chain
view, and at least two of the eight stating things no longer true. ovr.news's
`/ops/architecture` was 1,685 hand-drawn lines whose most recent commit was a
correction for naming a deleted scorer. **Deleted** (ovr `83e0b7c`).

**Framed as a signal path** because the project's vocabulary already was —
noise floor, band, operating point, gate, decay. Squelch, interpolator, matched
filter, compander.

- `architecture.html` — interactive drill-down block diagram, deep-linkable
  (`#nm/nm-score`), self-contained, no build step.
- Quarto prose pages; `chain/03-gates.qmd` written, eight stage stubs **marked
  as stubs**.
- `ops/make_snapshot.py` — a **level diagram** of the last cycle (article count
  at each tap), armed drop points, filter packages on disk, unit states.

**Hosting: sadalsuud over Tailscale, not GitHub Pages** — `veen-systems` is on
the free plan, where Pages serves public repos only, and this carries internal
host names and a defect inventory. Unit files in the repo, not only `/etc`
(FS#105). Refresh is a **timer, not an `OnSuccess=` off `nexusmind.service`**.

Live: `http://100.78.93.76:8099/`. LAN address refuses — verified.

## Part 3 — the review battery, which is the real content of this session

Six lenses. **Everything below was proven by execution, not by reading.**

### The site's only job is being true. It shipped 15 false claims.

- **"the one place articles are removed"** — there are several. ADR-022
  promises one drop point *per concern*; the page generalised it to an absolute.
- **The gate diagram drew the violence stamp BEFORE the load gate.** The code
  puts it after, and `main.py` carries a comment forbidding the drawn
  arrangement *because it was tried and was a no-op*. **The diagram reproduced
  the exact bug NM#281 fixed.**
- **"commerce is the only universal drop" is stale** — obituary has enforced
  since 2026-07-30. ADR-004 authorised one; two are running, and the ADR has
  not been amended.
- **FluxusSource load dedup is MD5 only.** MinHash and Jaccard have no
  non-test callers — `datasketch` installed for a feature that never runs.
- **The circuit breaker is keyed on the aggregator plugin, not the feed.**
- **Aegis reads a NexusMind-published Gist** of a derived artefact, not
  Contract B.
- **The editorial gate is disabled**, and **Ollama is primary, not Gemini**.
- **The rank formula has four factors and corroboration is not one.** There are
  *three different* rank formulas; the page merged them.
- **gpu-server is not scoring-only** — it runs the Ollama that summarises, a
  second stage of this chain, and the two `Conflicts=`.
- Dimension counts, filter counts, and **a stale status line in the README of
  an anti-staleness site.**

### Two verify commands returned a false all-clear

`grep -A6 <block>:` missed **every** `enforce:` key — they sit 10–17 lines
below their header, outside the window. The stage-order grep returned **nothing
at all**. Both were on the pages that catalogue this exact failure. Running the
three verify commands took under a minute and two of three were broken.

### The signature failure, committed three more times in my own work

1. **`systemctl show` on a nonexistent unit exits 0 with
   `ActiveState=inactive, Result=success`** — byte-identical to a healthy
   stopped unit. The snapshot rendered typo'd units as clean green rows. Fixed
   by querying `LoadState`.
2. **Image analysis cannot influence the dedup representative** although the
   selection code looks for its output — it runs *after* dedup and is never
   written back. Configured, reached, no effect.
3. **My own font-strip guard aborted the run when it succeeded.** `grep` exits
   1 when it finds nothing; under `set -euo pipefail` the check confirming
   success is what failed the unit.

### Security: the docs repo was a lateral-movement path

`refresh.sh` did `git pull` then `quarto render` on a 20-minute timer,
unhardened, as a user with **four passphraseless SSH keys** (including one to
the off-site backup store), write access to `app.yaml`, and the production
SQLite. **Quarto's `pre-render` hook is repo-controlled and executes shell** —
proven by executing it. `--ff-only` does not help. Hardening was on the *serve*
unit, which only reads files: exactly the wrong way round.

`refresh.sh`'s comment said it "touches nothing the pipeline owns and reads
everything read-only". That described intent. **A comment asserting safety is a
claim like any other** — occurrence noted.

Also: **every page view told Google the viewer's IP and the internal host's
address** via Quarto's bundled webfont `@import` — same class as the beacon
incident. Stripped, and the strip is checked.

### Then the hardening broke the service

`RestrictAddressFamilies=AF_INET AF_INET6` blocked `tailscale ip`, which reaches
the daemon over a **unix socket**. The lookup returned empty, `serve.sh`
correctly refused to fall back to `0.0.0.0`, and the unit sat in a restart loop
serving nothing — while **`systemctl is-active` reported "activating"**. Only
fetching a page revealed it.

### And the page rendered blank

An unescaped apostrophe I introduced in a text substitution. HTML still parsed;
every static check passed; the whole script died on a `SyntaxError` before
`render()` ran. Added **`ops/smoke_architecture.py`**, which drives real
chromium and asserts on the DOM at 11 routes — including `#%`, which threw
`URIError` and bricked the page permanently.

*That smoke test then produced a false failure of its own:* it staged in a
dot-directory, and **snap confinement does not grant access to hidden
directories in `$HOME`** (nor to the host's `/tmp` — snap has a private one).

## Carry forward

- **Mark chain links against *deliverables*, not issues.** A ✅ earned by one
  half of a bundled issue is indistinguishable from a finished one.
- **A verify command is code and can be wrong.** Two of three on a new site
  returned confident false all-clears. Run them when you write them.
- **Harden the unit that pulls and builds, not the one that reads.**
- Snap browsers: private `/tmp`, no dot-directories in `$HOME`.

## NEXT

1. **Decide the snapshot's enforcement table** — it publishes which gates are
   disarmed and at what threshold, to a tailnet spanning three accounts. It is
   also the most useful thing on the page. Owner call.
2. **pipeline-atlas #1** — fill the eight stage stubs, `06-measurement` first.
3. **pipeline-atlas #2** — cross-link from the four repos; get a stable
   Tailscale name before pasting an IP into four files.
4. **gpu-server was not probed** — the atlas claims it serves models "over
   HTTP" on the tailnet; if that endpoint is unauthenticated it is a finding.
5. FS#120 ~08-14, and re-measure corroboration precision on the capped system
   ~08-18.

## Related

- [[cross-repo-prioritization]] — Chains 1, 2, 16 corrected here
- [[project_session_2026_08_07]] — the morning half (seven owner decisions)
