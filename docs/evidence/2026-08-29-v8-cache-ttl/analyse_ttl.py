"""H-V8-8 — does the prompt-prefix cache survive the gap between corpus passes?

The readout that matters is NOT the aggregate hit rate: a whole-request hit and a prefix-only
hit both look like "high". They are told apart per row:
  * prefix-only  -> hit == the shared prefix, miss == this article's own tokens (hundreds+)
  * whole-request -> miss ~ 0
Revision 1 of this experiment could not tell them apart because its articles had been through
the same prompt the day before. Revision 2 uses articles never sent to any oracle under any v8
prompt.

Usage: python3 analyse_ttl.py <dir-with-Q0..Q3_out.jsonl>
"""
import json, sys
from pathlib import Path

D = Path(sys.argv[1])
LAGS = {0: "t+0", 1: "t+30 min", 2: "t+60 min", 3: "t+90 min"}
print(f"{'pass':<6}{'lag':<11}{'rows':>5}{'hit rate':>10}{'hit tokens (min..max)':>26}"
      f"{'miss tokens (min/med/max)':>28}{'cold-prefix rows':>18}")
prefix = None
for q in sorted(LAGS):
    f = D / f"Q{q}_out.jsonl"
    if not f.exists():
        continue
    rows = [json.loads(l) for l in open(f, encoding="utf-8")]
    u = [r["usage"] for r in rows if r.get("usage")]
    hit = sorted(x["prompt_cache_hit_tokens"] for x in u)
    miss = sorted(x["prompt_cache_miss_tokens"] for x in u)
    tot = sum(x["prompt_tokens"] for x in u)
    cold = sum(1 for m in miss if m > 5000)
    prefix = prefix or hit[len(hit) // 2]
    print(f"Q{q:<5}{LAGS[q]:<11}{len(u):>5}{100 * sum(hit) / tot:>9.1f}%"
          f"{f'{hit[0]:,}..{hit[-1]:,}':>26}{f'{miss[0]:,}/{miss[len(miss)//2]:,}/{miss[-1]:,}':>28}"
          f"{cold:>18}")
print(f"\nThe shared prefix is {prefix:,} tokens. A row whose hit EQUALS that and whose miss is "
      f"its own article\nlength is a PREFIX-only hit -- which is all a corpus pass can ever get, "
      f"since every article in one is new.")
