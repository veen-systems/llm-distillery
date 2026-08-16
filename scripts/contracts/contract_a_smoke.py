"""Contract A smoke test — run on sadalsuud against a delivered collection.

Answers one question: does the row a consumer receives carry what both schemas
say it does? Emission counts per block, plus validation against the producer's
own schema and NexusMind's Contract A.

Deliberately reports ABSENT and NULL separately: in `published`, null means
FABRICATED and absent means not-observed, and a counter that merges them
destroys the distinction the block exists to make.

⛔ `FIELDS EMITTED: n/18` IS NOT A COMPLETENESS SCORE, and a shortfall is not a
gap to chase. THREE fields are CONDITIONAL BY DESIGN and their absence is the
HEALTHY reading — the run that produced it is fine, not partial:

  - `fetch.charset_detected` and `fetch.charset_detected_confidence` — chardet is
    consulted ONLY when the strict UTF-8 rung fails
    (`FluxusSource/src/.../robust_feed_parser.py:938`). They are the #124
    diagnostic pair. Zero means no feed served non-UTF-8 bytes that run. Expect
    them near-zero permanently; they appear only on genuinely broken feeds.
  - `content_meta.error` — the extraction-failure key. Absent because nothing
    failed.

So 15/18 with exactly those three absent is a CLEAN result. Established by the
FluxusSource session 2026-08-16, on `collection_20260816_160729` (2,101 rows:
charset_used utf-8 1,990 / utf-8-sig 65, strict rung failed on zero rows).

This note lives here rather than in a memory file because the misreading happens
at the moment the output is read, not at the moment someone goes looking. Before
reporting any n/18 as a shortfall, name which field is missing and check whether
it is one of these three.
"""
import collections
import glob
import json
import sys

COLL = sys.argv[1] if len(sys.argv) > 1 else None
PROD_SCHEMA = '/home/jeroen/local_dev/FluxusSource/config/schemas/output_schema.json'
CONTRACT_A = '/home/jeroen/local_dev/NexusMind/contracts/fluxussource-output.schema.json'
CURRENT = '/home/jeroen/local_dev/FluxusSource/data/current'

if not COLL:
    COLL = sorted(glob.glob(f'{CURRENT}/collection_*'))[-1]
elif '/' not in COLL:
    COLL = f'{CURRENT}/{COLL}'          # accept a bare collection name

files = sorted(glob.glob(f'{COLL}/content_items_*.jsonl'))
rows = [json.loads(line) for fn in files for line in open(fn)]

# ⚠️ An empty read must RAISE, never report. Passing a bare collection name used
# to glob nothing, and the script then printed `0/18` plus `CLEAN (0 errors over
# 0 rows)` — a wrong path and a fully-conformant delivery are the same output,
# and the wrong one is the reassuring one. 2026-08-16.
if not rows:
    raise SystemExit(
        f"ABORT: 0 rows read from {COLL}\n"
        f"  content_items_*.jsonl matched: {len(files)} file(s)\n"
        f"  this is a bad path or an empty delivery, NOT a clean result")

print(f"collection : {COLL.rsplit('/', 1)[-1]}")
print(f"rows       : {len(rows)}")
print(f"source_type: {dict(collections.Counter(r.get('source_type') for r in rows))}")
print()

# ⚠️ DERIVED FROM THE SCHEMA, never hand-listed. The first version of this
# script hardcoded the field names and therefore reported 16/17 on a delivery
# that carried 17/18 — it could not see `fetch.charset_detected_confidence`,
# which shipped after the list was written. A hand-built population in the
# instrument measuring whether the contract is implemented: the same defect
# class this whole exercise exists to catch, one level up.
_SCHEMA = json.load(open(PROD_SCHEMA))
BLOCKS = {name: sorted(spec.get('properties', {}))
          for name, spec in _SCHEMA['properties'].items()
          if isinstance(spec, dict) and spec.get('type') == 'object'
          and spec.get('properties') and name != 'metadata'}

total_fields = emitted_fields = 0
for block, props in BLOCKS.items():
    present = [r for r in rows if isinstance(r.get(block), dict)]
    print(f"{block:14s} block on {len(present):5d}/{len(rows)} rows")
    for prop in props:
        total_fields += 1
        vals = [r[block][prop] for r in present if prop in r[block]]
        if not vals:
            print(f"    {prop:18s} ABSENT")
            continue
        emitted_fields += 1
        nulls = sum(1 for v in vals if v is None)
        dist = collections.Counter(
            str(v)[:28] for v in vals if v is not None).most_common(4)
        print(f"    {prop:18s} {len(vals):5d} values, {nulls} null | {dist}")
    print()

print(f"FIELDS EMITTED: {emitted_fields}/{total_fields}")
print()

try:
    import jsonschema
except ImportError:
    print("jsonschema unavailable — validation skipped")
    raise SystemExit(0)

for name, path in (('producer output_schema', PROD_SCHEMA), ('Contract A', CONTRACT_A)):
    try:
        schema = json.load(open(path))
    except OSError as exc:
        print(f"{name}: unreadable ({exc})")
        continue
    validator = jsonschema.Draft7Validator(schema)
    fails = collections.Counter()
    for r in rows:
        for err in validator.iter_errors(r):
            fails['/'.join(str(p) for p in err.absolute_path) or '<root>: ' + err.message[:60]] += 1
    version = schema.get('version', '?')
    print(f"{name} v{version}: {'CLEAN' if not fails else dict(fails.most_common(6))}"
          f"  ({sum(fails.values())} errors over {len(rows)} rows)")
