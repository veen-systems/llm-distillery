# Obituary-detector validation artifacts

Outputs of the scripts one directory up (`rollup_obit.py`, `panel_obit.py`,
`panel_audit*.py`, `eval_v5.py`). State and interpretation:
`memory/project-obituary-detector.md`.

## ⛔ Encoding, fixed 2026-09-06

`rollup_obit.json`, `rollup_obit_v3.json` and `rollup_june.json` were written as
**cp1252, not UTF-8**, so `Córdoba` and `Zusammenstoß` came back as invalid
continuation bytes and the files were not readable JSON. Cause: the writers called
`open(path, "w")` with no `encoding=`, taking the locale default — the same class of
defect as NexusMind#338 (`requests` returning `ISO-8859-1` for a charset-less
`text/*`). **Never let a default charset decide how bytes are written or read.**

- The three writers now pass `encoding="utf-8"` explicitly
  (`rollup_obit.py`, `panel_audit.py`, `panel_audit_deepseek.py`, `eval_v5.py`).
- `rollup_obit.json` and `rollup_obit_v3.json` were re-encoded cp1252 → UTF-8.
  The decoded content is **identical** — verified by parsing both and comparing the
  objects; only the byte encoding changed.

## ⚠️ `rollup_june.json.truncated`

That file is **not valid JSON and cannot be repaired**: the write was interrupted and
it ends mid-string, inside the `title` of a `recall_chk` row. It is preserved with a
`.truncated` suffix — re-encoded to UTF-8 like its siblings — so that it is no longer
scanned as JSON while its bytes stay in the tree. Nothing reads it; it is committed
history from `13b3805` (2026-07-10) and no complete version exists in git.
**Do not "fix" it by closing the brackets** — that fabricates the rows the write never
produced.
