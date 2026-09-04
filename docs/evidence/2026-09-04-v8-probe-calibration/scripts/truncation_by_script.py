"""How much of an article does each model actually SEE, by script?

The finding this exists for: non-Latin articles are SHORTER in characters and yet produce
MORE tokens, so more of each is cut at the 512-token limit — and Gemma is worse at it than
e5. Measured 2026-09-04 over all 6,590 corpus rows:

    e5-small   Latin 586 med tokens, 56.7% truncated, 87.4% of the article seen
    e5-small   non-Latin 694, 64.6%, 73.8%
    Gemma-3-1B Latin 574, 55.0%, 89.2%
    Gemma-3-1B non-Latin 843, 74.1%, 60.7%

⚠️ This measures truncation, not its consequence. That both this and the routing gap are
real does not establish that one causes the other; see MULTILINGUAL_REALITY.md §4.

Needs the corpus (gitignored, #97) — run on b650-gpu with venv-prodparity, from
~/llm-distillery, against datasets/ht_v8_corpus.jsonl.
"""
import json, collections, statistics as st
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
m = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
print("e5-small max_seq_length as ST configures it:", m.max_seq_length)
LIM = m.max_seq_length
tk_e5 = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small")
tk_g  = AutoTokenizer.from_pretrained("google/gemma-3-1b-pt")
by = collections.defaultdict(lambda: collections.defaultdict(list))
for line in open("datasets/ht_v8_corpus.jsonl", encoding="utf-8"):
    r = json.loads(line)
    txt = (r.get("title") or "") + "\n\n" + (r.get("content") or "")
    g = "non-Latin" if r.get("non_latin") else "Latin"
    by[g]["e5"].append(len(tk_e5(txt, add_special_tokens=False, truncation=False)["input_ids"]))
    by[g]["gemma"].append(len(tk_g(txt, add_special_tokens=False, truncation=False)["input_ids"]))
for enc, lim in (("e5", LIM), ("gemma", 512)):
    print("\n%s tokenizer, limit %d:" % (enc, lim))
    print("  %-11s %11s %20s %22s" % ("group","med tokens","% truncated","median %% of article seen"))
    for g in ("Latin","non-Latin"):
        t = by[g][enc]
        trunc = 100*sum(1 for x in t if x > lim)/len(t)
        seen = st.median([min(1.0, lim/x) for x in t])
        print("  %-11s %11.0f %19.1f%% %21.1f%%" % (g, st.median(t), trunc, 100*seen))
