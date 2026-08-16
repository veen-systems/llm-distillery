"""Contract A smoke test — run on sadalsuud against a delivered collection.

Answers one question: does the row a consumer receives carry what both schemas
say it does? Emission counts per block, plus validation against the producer's
own schema and NexusMind's Contract A.

Deliberately reports ABSENT and NULL separately: in `published`, null means
FABRICATED and absent means not-observed, and a counter that merges them
destroys the distinction the block exists to make.
"""
import collections
import glob
import json
import sys

COLL = sys.argv[1] if len(sys.argv) > 1 else None
PROD_SCHEMA = '/home/jeroen/local_dev/FluxusSource/config/schemas/output_schema.json'
CONTRACT_A = '/home/jeroen/local_dev/NexusMind/contracts/fluxussource-output.schema.json'

if not COLL:
    COLL = sorted(glob.glob('/home/jeroen/local_dev/FluxusSource/data/current/collection_*'))[-1]

rows = [json.loads(line)
        for fn in sorted(glob.glob(f'{COLL}/content_items_*.jsonl'))
        for line in open(fn)]

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
