# DeepSeek V4.1 Flash price cut — the sources, archived 2026-09-09

Why this directory exists: on the day the cut was announced, **the vendor pricing
page contradicted the announcement** — it still carried the V4 card, because the
new rates take effect at 04:00 UTC 2026-09-10. So for one day the only source for
the numbers now recorded in `memory/oracle-pricing-scheduling.md` was an email.
Both sides are frozen here so the disagreement is checkable later.

## What is here

| file | what it is |
|---|---|
| `announcement-body.html` | the decoded `text/html` part of the announcement email |
| `announcement-headers.txt` | its headers, and the MIME structure |
| `pricing-page-2026-09-09.html` | `https://api-docs.deepseek.com/quick_start/pricing/` as fetched 2026-09-09 20:04 local — **still the V4 card** |
| `oracle_cost-2026-09-09.txt` | `scripts/analysis/oracle_cost.py` output under the new card |

⚠️ **The raw `.eml` is NOT here.** It was read from
`~/Downloads/Announcement on DeepSeek V4.1 Flash API Pricing 2026-09-09T18_51_34+02_00.eml`
at 20:03 local; when it was copied here at 20:13 the file was gone from `~/Downloads`
(directory mtime 20:06). Nothing in this session deleted it — the file was only ever
opened read-only. What is archived is the decoded body and the headers as printed at
20:03, not the original bytes. **Treat the headers file as a transcript, not as the
message.** If the original still exists in the mail client, re-export it over
`announcement-headers.txt`'s claim.

## The announcement, in one paragraph

DeepSeek releases **V4.1 Flash** around 2026-09-10 (Beijing time). Until V4.1 Pro
ships, **all requests to the Pro model are routed to V4.1 Flash and billed at Flash's
price.** New pricing takes effect **04:00 UTC, 2026-09-10**.

| $/1M tokens | off-peak | peak |
|---|---|---|
| input, cache hit | 0.003 | 0.006 |
| input, cache miss | 0.15 | 0.3 |
| output | 0.6 | 1.2 |

Peak hours **unchanged**: 01:00–04:00 and 06:00–10:00 UTC, Monday–Friday; all other
hours off-peak.

## What it changes

Recorded in full in `memory/oracle-pricing-scheduling.md` (top block). The short form:

- **~30% cheaper at every measured prompt shape** (0.697×–0.712× of the V4 card).
- **The crossover argument is abolished, not re-derived.** Cache-miss input becomes
  `$0.15/M` — *exactly* Gemini Batch's input rate — while output drops to `$0.60`
  against Batch's `$1.25`. DeepSeek therefore ties at worst on input and wins on
  output, at every shape and every cache rate. The unconditional flip point goes
  **32.9% → 0.0%**. ⛔ The `I/O < 8.4` ratio and the 19.0–26.5% per-shape flip points
  are properties of the **V4** card; do not re-quote them.
- **DeepSeek peak now undercuts Gemini realtime** (1.12×–1.22×), so "peak is
  unambiguously wrong" no longer holds. Off-peak is still half, and still free to
  obtain (weekends bill off-peak entirely).
- **Gemini Batch is still a price we cannot pay** — no `.batches` call site. Unchanged.

## What it does NOT settle — #157

We call the **`deepseek-chat` alias**, not a pinned id, because the literal id enables
reasoning mode and returns empty `content`. The alias resolves server-side, so the
oracle's labelling function changed at the cutover **with no code change and nothing in
any row or log recording which model scored it**. ADR-010 ranks oracle consistency above
cost. No V4-vs-V4.1 parity run exists. See llm-distillery#157.

## Reproduce

```bash
PYTHONPATH=. python3 scripts/analysis/oracle_cost.py     # rate card + per-shape table
curl -sL https://api-docs.deepseek.com/quick_start/pricing/ | grep -o '0\.1[0-9]*'
```

At time of archiving, `GET https://api.deepseek.com/models` returned three ids —
`deepseek-v4-flash`, `deepseek-v4-pro`, `deepseek-v4-flash-vision-exp` — i.e. **V4.1 had
not landed yet.** That also refutes the "exactly two ids" claim recorded 2026-08-14; the
substantive half of it (no lighter tier to retreat to) still holds, since vision-exp is
priced identically to flash.
