"""Blind harm panel for the Thriving lens — would a reader be harmed seeing this here?

Adapted from docs/evidence/2026-09-08-v8-live-panel/judge.py (EXP-029). Changes: the rubric
asks the HARM question rather than the scope question, verdicts are graded, and it repeats k
times per article for a majority vote (#135: a single pass is a coin toss on the boundary).

⛔ THE JUDGE IS BLIND. It sees only title and body — never which lens surfaced the article,
never either lens's score, never the stratum. The caller must not add them to the payload.

⛔ THE RUBRIC IS NEITHER LENS'S ORACLE PROMPT. It is built from the READER-FACING promise of
the Thriving tab in ovr.news (`src/i18n/translations.ts`):
    "People thriving, health, connection"
    "Health improving, rights advancing, lives getting better."
Grading v7 on v8's rubric (or the reverse) is the confound the NexusMind session hit and
flagged; v7's oracle is Gemini Flash and v8's is DeepSeek, so the rubric must belong to
neither and BOTH families must judge.

Usage:
  python3 judge.py <in.jsonl> <out.json> <endpoint> <model> <keyname> <k>
"""
import json, os, sys, time, configparser, urllib.request
from collections import Counter

RUBRIC = """A news site has a tab called "Thriving". Readers are told it contains:

    "Health improving, rights advancing, lives getting better."
    "People thriving, health, connection."

Readers open this tab specifically to step away from a relentless feed of crisis and harm.

Judge ONE article against that promise. Ask what a reader would feel on opening it there.

- harmful    : the dominant subject is a HARM — a crime, abuse, trafficking, exploitation,
               killing, death, disaster, war, or a worsening condition. Even where an
               enforcement action, rescue or conviction is genuinely good news, the article
               is ABOUT the harm, and a reader who came for relief meets it unprepared.
- misleading : not harmful, but it does not deliver the promise — nothing has actually
               improved for people yet. A plan, proposal, pledge, draft law, launch,
               announcement, appointment, study or research finding with no delivered effect.
- weak       : genuinely on-promise but thin — a real improvement for people that is minor,
               very local, or barely evidenced.
- fits       : delivers the promise — a concrete improvement in health, rights, or people's
               lives that has ACTUALLY HAPPENED for identifiable people.

`fits` is not the default. If you cannot name who is better off and how, it is not `fits`.
Judge the article as a whole, not its most positive sentence.

Reply with ONLY a JSON object: {"verdict": "...", "why": "<=15 words"}"""

VALID = {"harmful", "misleading", "weak", "fits"}


def main():
    inp, outp, endpoint, model, keyname, k = sys.argv[1:7]
    k = int(k)
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
                if r.get('verdict') not in (None, 'ERROR'):
                    done[(r['id'], r['pass'])] = r
        print(f'  resuming: {len(done)} judgements already on disk', file=sys.stderr)

    fh = open(ckpt, 'a'); out = []; consec = 0
    for i, it in enumerate(rows):
        # BLIND: only these two fields ever reach the model.
        prompt = f"{RUBRIC}\n\nTITLE: {it['title']}\n\nBODY:\n{it['content']}\n\nJSON:"
        votes = []
        for p in range(k):
            if (it['id'], p) in done:
                votes.append(done[(it['id'], p)]); continue
            v, why = 'ERROR', ''
            for attempt in range(3):
                try:
                    req = urllib.request.Request(endpoint,
                        data=json.dumps({"model": model, "temperature": 1.0,
                                         "messages": [{"role": "user", "content": prompt}]}).encode(),
                        headers={"Authorization": f"Bearer {key}",
                                 "Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=120) as r:
                        t = json.loads(r.read())["choices"][0]["message"]["content"].strip()
                    t = t[t.find('{'):t.rfind('}') + 1]
                    d = json.loads(t)
                    v = d.get('verdict', 'ERROR')
                    if v not in VALID:
                        v = 'ERROR'; why = f'unrecognised verdict {d.get("verdict")!r}'
                    else:
                        why = d.get('why', '')[:80]
                    break
                except Exception as e:
                    why = str(e)[:70]; time.sleep(2 * (attempt + 1))
            consec = consec + 1 if v == 'ERROR' else 0
            if consec >= 5:
                print('ABORT: 5 consecutive errors — ' + why, file=sys.stderr)
                fh.flush(); sys.exit(3)
            rec = {'id': it['id'], 'pass': p, 'verdict': v, 'why': why}
            votes.append(rec); fh.write(json.dumps(rec) + '\n'); fh.flush()
        good = [r['verdict'] for r in votes if r['verdict'] != 'ERROR']
        tally = Counter(good)
        out.append({'id': it['id'], 'votes': [r['verdict'] for r in votes],
                    'majority': tally.most_common(1)[0][0] if good else 'ERROR',
                    'unanimous': len(tally) == 1 and len(good) == k,
                    'whys': [r['why'] for r in votes]})
        if (i + 1) % 20 == 0:
            print(f'  {i+1}/{len(rows)}', file=sys.stderr, flush=True)
    json.dump(out, open(outp, 'w'), indent=1)
    errs = sum(1 for r in out if r['majority'] == 'ERROR')
    print(f'wrote {len(out)} articles ({k} passes each), {errs} unusable', file=sys.stderr)


if __name__ == '__main__':
    main()
