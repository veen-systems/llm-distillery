# Session 2026-09-17 (late) — `/audit-context`: a control that could never stop firing, and a cap I shipped without a mechanism

**Shape of the session:** a structural audit that turned into two instrument repairs.
`$0 spend`, no oracle calls, no GPU, nothing in `filters/`. **Deploy N/A — inapplicable,
not skipped**: no filter package, model, calibration, threshold or probe changed.
**Merge N/A** — worked on `main`, no branch. Commits `ad32356` + this one, pushed.

## The keeper — a shape test inside an existence-test disjunction

`refcheck.py`'s STALE-placeholder test asks *"is this marked path actually THERE?"* through a
disjunction of rungs. Every rung in it is an existence test except `rung3`, which is
`frag.startswith(STATE_DIRS)` — a **shape** test no file system can falsify. So every
angle-segment path under a state directory was ruled STALE unconditionally, and the author had
**no legal move**: the angle form is mandatory for a variable segment.

⭐ **The coupling was ALREADY MEASURED — 2026-08-16, in a comment in that same file** (*"findings
went 1 → 4 … the two mechanisms are alternatives, never both"*) — **and the remedy chosen was to
delete the three markers.** That satisfies a test that cannot stop matching, so it bought silence
until someone wrote a state path again. They did, four times, 2026-09-07..09-10.

⚠️ **The tell for wolf-crying is not "it keeps coming back" — it is "no input could make it
stop."** Fixed by excluding rung 3 at that one site; it stays live in the main ladder.

## Three of my own errors, all caught by controls rather than by reading

1. **I ran the wrong checker.** The skill's literal command names the framework's `refcheck.py`;
   this repo has a 1,629-line **fork**, recorded as a deliberate partial adoption. Framework: 216
   findings. Fork: 23. ⛔ Both correct — and I was one sentence from reporting "references
   regressed 1 → 216", sending the reader after a regression that does not exist.
2. **I capped a file and shipped nothing that holds the cap.** Found while writing the #133
   comment, not while doing the work: the sentence *"remedy applied, not just diagnosed"* would
   not finish honestly. Now mechanized, 4 tests, mutation-proven.
3. **My "does the target already hold this?" check reported three atoms ABSENT** before I trimmed
   the auto-memory index. The grep was **case-sensitive**; all three were present
   (`blast radius`, `A DENYLIST IS ONE`, and a 2026-09-11 entry). Had I trusted it I would have
   rewritten content that already existed — or, worse, trusted its inverse and cut something real.

## Reference integrity: 23 → 0, and what the 0 does NOT cover

Each of the 23 triaged individually: 3 false STALEs (above), **1 genuine** stale marker — an
entry asserting *"none of them resolve in this estate"* while naming the resolving path in its
own sentence — 19 moved into the **counted** placeholder section (35 → 54), 2 into RESOLVED.
Asserted positively per section; absence from FINDINGS proves nothing. Zero is not the target, so
the checker was re-proven alive on the **real corpus** afterwards with seeded local and
cross-repo fabrications, both caught, then removed.

⛔ **SCOPE: that 0 is the DEFAULT scan set** — `CLAUDE.md` + `memory/*.md` + the auto-memory
index. `--docs` is opt-in, so **167 `docs/` files were excluded**, where the same instrument
reports **376**. Re-measured for LD#134: **338 → 376 in 20 days, and +34 of the +37 is FROZEN**
(`evidence/`, `decisions/` — append-only records that are correct as history). That split
strengthens #134's existing tiering proposal rather than being a new alarm.

## The layer budget, and why the attribution was the finding

55,459 → **50,164 B**. Since #138's baseline, 19 days, same author:

| file | capped? | growth |
|---|---|---|
| `CLAUDE.md` | yes | +355 B — **~19 B/day** |
| auto-memory `MEMORY.md` | no | +7,021 B — **~370 B/day** |

⚠️ The auto-memory figure is **derived** by subtraction from #138's recorded total, not a dated
series. Order of magnitude, not a trend line.

The file everyone watches behaved; the one nobody watches drove the layer over its budget alone.
Every target was verified to hold the cut content **first** (#133's routing rule), and the link
set is byte-identical before and after, so no memory became unreachable.

## Step 8 (retirement) — the item `docs/TODO.md` queued

**The real finding is that the answer had to be EXCAVATED from seven audit commit messages**,
because no prior audit ever recorded step→finding. That gets harder every audit. Record and the
standing rule: `docs/decisions/2026-09-17-audit-step-attribution.md`.

⛔ **Step 7 (gitignore) has caught nothing in its whole history — recorded as a retirement
candidate NOT retired.** It has a plausible prevention story, the class is covered nowhere else,
and its cost is one `git ls-files` a month. Release condition is in the file. Step 3 likewise.

## Dropped from my own plan after checking

`CLAUDE.md:302`'s `/home/jeroen/local_dev/...` is not wrong-layer data — it is
`fit_normalization.py`'s own default, live on sadalsuud, in 11 places. Editing `CLAUDE.md` alone
would have made it the one site that disagrees. And `eval_ht_v8.py`, which I called a lost
instrument behind an open hypothesis, has its location recorded at
`docs/evidence/2026-09-06-v8-deploy-gate/README.md:121` (b650, `~/llm-distillery/`).

## Verified

refcheck 0 findings / 22 shapes named · sensitivity **38/38**, three live mutations ·
**797 unit tests pass**, 17 skipped · `check_doc_claims` 5/5 · `check_claim_shapes` 25/25 ·
all four budget guards PASS.

## Next session

- **Framework is 6 releases behind and the stamp is deliberately NOT bumped** — 5 adopt items in
  `docs/TODO.md`, `#166` and `#136` first, `## Mechanized` into the gotcha log, stamp LAST.
- **LD#134 step 2** (tier `docs/`, decide whether `--docs` comes off the flag) is now the
  best-evidenced item on the board: 376 findings, 43% frozen and climbing at ~8× the live rate.
- **The retracted 19.9%/13.0% framing** still sits at `CLAUDE.md:74` plus three copies.
- **#160**'s two Dutch-name violations are still open.
