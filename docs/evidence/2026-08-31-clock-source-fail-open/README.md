# A guard that reported a detection as a transport failure — and the claim it was guarding is obsolete

**2026-08-31. $0** — read-only, on the collection host. No model, no filter, no threshold, no
probe, nothing under `filters/`, nothing deployed. Found while running the routine verify battery
before committing unrelated work: `run_verify_annotations.py` reported **`errored=1`**, and the
one error was worth more than the session that surfaced it.

## 1. What the battery said, and why it was a lie in both directions

```
CANNOT VERIFY memory/date-error-recency-boost-hypotheses.md #1  CANNOT VERIFY: remote check did not run
```

Run by hand, `scripts/verification/check_clock_source_partition.sh` printed **this**, in this
order, and exited **0**:

```
MIXED CASES: {'api->utc': 134, 'rss->utc': 3239, 'social->utc': 13}
CANNOT VERIFY: remote check did not run
exit=0
```

⛔ **The check ran, found a violation, printed the violation's own evidence, and then denied
running** — because the remote block's `sys.exit(1)` and an unreachable host landed in the **same
`||` branch**:

```bash
ssh … python3 - <<'PY' 2>/dev/null || { echo "CANNOT VERIFY: remote check did not run"; exit 0; }
```

⭐ **A detection was indistinguishable from a transport failure, and it presented as the harmless
one.** Same shape as three others repaired on 2026-08-29 — `check_prod_filters_table.sh` exiting 0
on `FAIL`, `| grep` discarding `oracle_cost.py`'s `return 1`, and `| tail -4; echo $?` reporting
*tail's* status — now `||` swallowing an exit code it did not distinguish. ⛔ **No ordinal is
stated here on purpose**: a count offered to make a point about recurrence is the thing that goes
stale, and `memory/gotcha-log.md` carries the catalogue. ⚠️ **They are one defect written four
ways: a wrapper that cannot tell "it said no" from "it did not speak."**

## 2. What the violation actually was — the claim is obsolete BY SUCCESS

`memory/date-error-recency-boost-hypotheses.md` records, as a ⭐ finding measured over four
deliveries on 2026-08-15/16, an exact **partition**: `api → host_local`, `rss`/`social` → `utc`,
**not one mixed case in ~9,800 rows**. The guard encodes that partition, so today's rows read as
mixed.

They are not mixed. **They are all `utc`** — census over every collection retained on the host
([`census.txt`](census.txt), produced by the committed
[`census_clock_source.py`](census_clock_source.py)):

```
window: 47 collections, collection_20260824_040945 .. collection_20260831_200757
rows: 158,656   unstamped: 0
pairs: {'api->utc': 5512, 'rss->utc': 152774, 'social->utc': 370}
```

**Zero `host_local`, zero unstamped, across 158,656 rows.** FS#176's migration is complete: the
2h host-clock skew is gone from delivered rows, not hiding behind a stamp.

⭐ **And the stamp is TRUTHFUL, which is the half a pair table cannot show.** A `utc` stamp on a
host-local timestamp would be strictly worse than the original skew, because every consumer
downstream trusts the stamp instead of the number. Checked directly — `collected_date` against
each collection's own UTC start, on the oldest, middle and newest directory:

| delivery | api | rss | social |
|---|---|---|---|
| `…0824_040945` | −5.4 min | −5.4 … −2.2 | −5.4 |
| `…0828_001032` | −5.5 | −5.7 … −2.5 | −5.4 |
| `…0831_200757` | −5.4 | −5.5 … −2.5 | −5.2 |

A host-local clock on this host reads **+120 minutes**. Every median is within six minutes of
zero, `api` included. ⚠️ The offsets are consistently *negative* by ~5 minutes, which this run
does **not** explain — most likely the directory name is stamped when a collection ends rather
than when it starts. It is recorded rather than smoothed over; it is two orders of magnitude away
from the 120 the question turns on.

⚠️ **The window is part of this source, and it cannot date the change.** `data/current` retains
~8 days; the oldest directory on disk (2026-08-24) is *already* fully `utc`. The flip happened at
or before then, and nothing in this population can say when. ⛔ Do not write "changed on
2026-08-24" anywhere.

## 3. What was changed

**The assertion**, from a partition to the post-migration invariant — *every row stamped, every
stamp `utc`, zero `host_local`*. This is **strictly stronger** than the partition and falsifiable
the same way: one `host_local` row refutes it. The old assertion, its date, and the evidence that
retired it are kept in the script's own header, because a guard whose history is erased cannot be
audited.

**The fail-open.** Exit codes are now carried out of the remote block — `0` holds, **`2`
violation → the wrapper prints `FAIL:` and exits 1**, `3` cannot-verify — and an ssh failure that
returns anything else says so *and names its own return code*.

⚠️ **Applying the working rule *"a failing check may be the control working — never fix it before
asking what it proves"*:** what this one's failure was buying was **nothing**. It exited 0 with a
message denying it had run, so no caller could act on it. That is what made updating the
expectation safe — not the fact that the new state looks tidy.

## 4. The controls — the FAIL branch is proven, not asserted

`FS_COLLECTION_ROOT` exists so the shipped script can be pointed at a seeded fixture. It defaults
to production and the `<!-- verify: -->` annotation passes no environment, so **the shipped path
is the tested path**.

⚠️ **The seam is a hazard and it is handled, not waved at.** The battery runs the guard as a
subprocess, so it **inherits the environment** — a stray `FS_COLLECTION_ROOT` would silently
redirect the check and still print `PASS`. Verified, not assumed: setting it made the whole
battery turn red on a seeded fixture (`failed=1`, runner exit 1). The verdict line therefore
**names the directory it read**, so a redirect is visible in the output rather than inferable:

```
PASS every row utc, 3386/3386 stamped in /home/jeroen/local_dev/FluxusSource/data/current/collection_20260831_200757: {...}
PASS every row utc, 1/1 stamped in /tmp/clkfix2/collection_20260831_999999: {'rss->utc': 1}
```

| control | output | exit |
|---|---|---|
| one `host_local` row seeded among two `utc` | `FAIL: 0 unstamped, 1 host_local, 0 other — {'api->host_local': 1, 'api->utc': 1, 'rss->utc': 1}` | **1** |
| collection directory with no rows | `CANNOT VERIFY: newest collection has no rows` | 0 |
| rows present, none stamped | `CANNOT VERIFY: no row carries collected.clock_source — pre-deploy data` | 0 |
| root does not exist | `CANNOT VERIFY: sadalsuud unreachable, or no collection_* under /tmp/clkfix_nope` | 0 |
| **production, unchanged** | `PASS every row utc, 3386/3386 stamped in …/collection_20260831_200757: {'api->utc': 134, 'rss->utc': 3239, 'social->utc': 13}` | 0 |

⭐ **And the outcome was proven at the CALLER, not at the script** — naming a caller is not
checking one. With the violating fixture in place, the whole battery reports it:

```
FAIL   memory/date-error-recency-boost-hypotheses.md #1  FAIL: 0 unstamped, 1 host_local, 0 other in … — {'api->host_local': 1, 'rss->utc': 1}
blocks found: 46  |  passed=20  failed=1  errored=0  …          runner exit=1
```

Against `failed=0`, `errored=0`, runner exit 0 on the same command with the fixture removed.

Exit status captured directly, never through a pipe. Fixtures were removed from the host after
the run.

## 5. Reproduce

```bash
bash scripts/verification/check_clock_source_partition.sh; echo "exit=$?"

scp docs/evidence/2026-08-31-clock-source-fail-open/census_clock_source.py sadalsuud:/tmp/
ssh sadalsuud 'python3 /tmp/census_clock_source.py'
```

⚠️ `census_clock_source.py` hard-codes **CEST (UTC+2)** and goes stale at the CET switch on
**2026-10-25** — the same class of bug it exists to find. It says so at the bottom of its own
source.
