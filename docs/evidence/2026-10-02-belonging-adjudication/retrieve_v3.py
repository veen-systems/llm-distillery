"""Belonging retrieval: embed the corpus once, then rank by centroid and by nearest-seed similarity (b650 GPU).

    python retrieve_v3.py seeds.jsonl corpus.jsonl outdir

Reuses scripts/screening/embedding_screener.py's text recipe (title + first 1,024 chars, "query: " prefix,
multilingual-e5-small, normalised) and its OFF_LENS mask, imported from a copy next to this file. Writes
outdir/emb.npy (corpus, float16), outdir/ids.json, and outdir/scores.jsonl: id, raw, centroid, maxsim, nearest_seed."""
import json, os, sys
import numpy as np
from sentence_transformers import SentenceTransformer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from embedding_screener import article_to_text, embed_batch, is_off_lens

seeds = [json.loads(l) for l in open(sys.argv[1])]
corpus = [json.loads(l) for l in open(sys.argv[2])]
out = sys.argv[3]
os.makedirs(out, exist_ok=True)
model = SentenceTransformer('intfloat/multilingual-e5-small')
S = embed_batch(model, [article_to_text(a) for a in seeds])
emb_path = os.path.join(out, 'emb.npy')
if os.path.exists(emb_path):
    E = np.load(emb_path).astype(np.float32)
    assert E.shape[0] == len(corpus), 'cached embeddings do not match the corpus'
else:
    E = embed_batch(model, [article_to_text(a) for a in corpus], batch_size=512)
    np.save(emb_path, E.astype(np.float16))
c = S.mean(axis=0)
c /= np.linalg.norm(c)
cent = E @ c
sims = E @ S.T
maxsim, nearest = sims.max(axis=1), sims.argmax(axis=1)
with open(os.path.join(out, 'scores.jsonl'), 'w') as f:
    for a, ce, ms, nn in zip(corpus, cent, maxsim, nearest):
        f.write(json.dumps(dict(id=a['id'], raw=a.get('raw'), off_lens=is_off_lens(a), centroid=round(float(ce), 4),
                                maxsim=round(float(ms), 4), nearest_seed=seeds[nn]['id'])) + '\n')
print(len(corpus), 'scored')
