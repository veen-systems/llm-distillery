import json, os, sys, time, configparser, urllib.request
# arms: family (endpoint+model) x prompt (rubric) x truncation
RUBRIC = """You are classifying news articles for a lens called "human thriving".

Emit ONE verdict per article, using these definitions EXACTLY. `in_scope` is NOT the default —
if you cannot name a concrete process that is going well FOR PEOPLE, NOW, it is not in_scope.

- in_scope        : a process is going well for people, now; benefit has actually been delivered
- harm_is_subject : the dominant subject OR THE OCCASION is a harm, crime, bereavement, abuse,
                    worsening statistic or institutional failure
- response_to_harm: the only good news is a RESPONSE to a harm (a fund, a helpline, an arrest,
                    a pledge), not repair actually delivered to people
- no_person_benefits: the benefit reaches an animal, an institution, a market, a building or a
                    jurisdiction — not a person
- out_of_scope    : nothing has taken effect yet — a proposal, draft law, plan, or preparation

Reply with ONLY a JSON object: {"verdict": "...", "why": "<=15 words"}"""

inp, outp, endpoint, model, keyname, trunc = sys.argv[1:7]
trunc = int(trunc)
cp = configparser.ConfigParser(); cp.read('config/credentials/secrets.ini')
key = cp.get('api_keys', keyname)
rows = [json.loads(l) for l in open(inp) if l.strip()]

ckpt = outp + '.partial.jsonl'
done = {}
if os.path.exists(ckpt):
    for line in open(ckpt):
        line = line.strip()
        if line:
            r = json.loads(line)
            if r.get('verdict') not in (None, 'ERROR'):   # an ERROR is NOT a result
                done[r['id']] = r
    print(f'  resuming: {len(done)} already judged', file=sys.stderr)

fh = open(ckpt, 'a'); out = []; consec = 0
for i, it in enumerate(rows):
    if it['id'] in done:
        out.append(done[it['id']]); continue
    body = it['content'] if trunc <= 0 else it['content'][:trunc]
    prompt = f"{RUBRIC}\n\nTITLE: {it['title']}\n\nBODY:\n{body}\n\nJSON:"
    v, why = 'ERROR', ''
    for attempt in range(3):
        try:
            req = urllib.request.Request(endpoint,
                data=json.dumps({"model": model, "temperature": 1.0,
                                 "messages": [{"role": "user", "content": prompt}]}).encode(),
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                t = json.loads(r.read())["choices"][0]["message"]["content"].strip()
            t = t[t.find('{'):t.rfind('}') + 1]
            d = json.loads(t); v = d.get('verdict', 'ERROR'); why = d.get('why', '')[:80]
            break
        except Exception as e:
            why = str(e)[:70]; time.sleep(2 * (attempt + 1))
    consec = consec + 1 if v == 'ERROR' else 0
    if consec >= 5:
        print('ABORT: 5 consecutive errors — ' + why, file=sys.stderr); fh.flush(); sys.exit(3)
    rec = {'id': it['id'], 'verdict': v, 'why': why}
    out.append(rec); fh.write(json.dumps(rec) + '\n'); fh.flush()
    if (i + 1) % 20 == 0: print(f'  {i+1}/{len(rows)}', file=sys.stderr, flush=True)
json.dump(out, open(outp, 'w'), indent=1)
errs = sum(1 for r in out if r['verdict'] == 'ERROR')
print(f'wrote {len(out)} verdicts, {errs} ERROR', file=sys.stderr)
