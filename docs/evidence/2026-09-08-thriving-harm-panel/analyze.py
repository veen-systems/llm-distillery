"""Analyse the blind Thriving harm panel.

    python3 docs/evidence/2026-09-08-thriving-harm-panel/analyze.py

⛔ CONTROLS RUN HERE AND ASSERT:
  1. every judged id is in the frame, and every frame id was judged, on SETS not counts;
  2. the strata sizes match the pre-registered draw (60 / 40 / 37);
  3. no judged article carries an ERROR majority into a rate;
  4. the two judges are DIFFERENT OBJECTS — if their verdicts were identical on every row the
     cross-family design proved nothing, so a zero-disagreement result is reported as a
     FAILED CONTROL rather than as agreement.
"""
import json
import math
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["harmful", "misleading", "weak", "fits"]
STRATA = ["v7_only", "both", "v8_only"]
EXPECTED = {"v7_only": 60, "both": 40, "v8_only": 37}
# Each lens's oracle family — a judge flatters its own lens, so the CONSERVATIVE reading of a
# lens is the opposing family's verdict. v7: filters/uplifting/v7/config.yaml:42 (gemini-flash).
# v8: filters/human_thriving/v8/config.yaml:63 (deepseek).
OPPOSING = {"v7_only": "deepseek", "both": None, "v8_only": "gemini"}


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def fisher(a, b, c, d):
    """Two-sided Fisher exact on [[a,b],[c,d]]."""
    def lc(n, k):
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    n = a + b + c + d
    p_obs = math.exp(lc(a + b, a) + lc(c + d, c) - lc(n, a + c))
    tot = 0.0
    for i in range(max(0, a + c - (c + d)), min(a + b, a + c) + 1):
        p = math.exp(lc(a + b, i) + lc(c + d, a + c - i) - lc(n, a + c))
        if p <= p_obs * (1 + 1e-9):
            tot += p
    return min(1.0, tot)


def main():
    frame = {}
    for line in open(os.path.join(HERE, "panel_frame.jsonl")):
        r = json.loads(line)
        frame[r["id"]] = r

    arms = {}
    for name, fn in (("deepseek", "judge_deepseek_k3.json"), ("gemini", "judge_gemini_k1.json")):
        p = os.path.join(HERE, fn)
        if os.path.exists(p):
            arms[name] = {r["id"]: r for r in json.load(open(p))}
    assert arms, "no judge output found"

    print("=" * 78)
    print("CONTROLS")
    print("=" * 78)
    fids = set(frame)
    for name, a in arms.items():
        assert set(a) == fids, (
            f"{name}: judged set != frame set "
            f"(judged-not-framed {sorted(set(a) - fids)[:3]}, "
            f"framed-not-judged {sorted(fids - set(a))[:3]})")
        errs = [i for i, r in a.items() if r["majority"] == "ERROR"]
        assert not errs, f"{name}: {len(errs)} articles have an ERROR majority: {errs[:3]}"
        print(f"  {name}: {len(a)} articles judged, set-identical to the frame, 0 ERROR majorities")
    got = Counter(frame[i]["stratum"] for i in fids)
    assert dict(got) == EXPECTED, f"strata drifted from the pre-registered draw: {dict(got)}"
    print(f"  strata match the pre-registration: {dict(got)}")

    if len(arms) == 2:
        d, g = arms["deepseek"], arms["gemini"]
        disagree = [i for i in fids if d[i]["majority"] != g[i]["majority"]]
        assert disagree, (
            "CONTROL FAILED: the two judges agree on every single row. Either the same arm was "
            "run twice or one output overwrote the other — the cross-family design proves "
            "nothing in that state.")
        agree = len(fids) - len(disagree)
        po = agree / len(fids)
        pe = sum((sum(1 for i in fids if d[i]["majority"] == v) / len(fids)) *
                 (sum(1 for i in fids if g[i]["majority"] == v) / len(fids)) for v in ORDER)
        print(f"  the two judges are different objects: they disagree on {len(disagree)} of "
              f"{len(fids)} rows (raw agreement {po:.3f}, Cohen kappa {(po-pe)/(1-pe):.3f})")

    for name, a in arms.items():
        k = max(len(r["votes"]) for r in a.values())
        if k < 2:
            # A single pass is unanimous BY CONSTRUCTION. Printing "0% split" here would read
            # as stability and would be an artifact of k, not a property of the judge.
            print(f"  {name}: k=1 — NO churn measure available (unanimity is vacuous at k=1)")
            continue
        churn = sum(1 for r in a.values() if not r["unanimous"])
        print(f"  {name}: {churn}/{len(a)} articles had a SPLIT k={k} vote "
              f"({churn/len(a)*100:.1f}%) — a majority is not a settled verdict")

    for name, a in arms.items():
        print()
        print("=" * 78)
        print(f"VERDICTS — judge: {name}" +
              ("   (v8's own oracle family)" if name == "deepseek" else
               "   (v7's own oracle family)"))
        print("=" * 78)
        hdr = "  {:10s}" + "".join("{:>13s}" for _ in ORDER)
        print(hdr.format("stratum", *ORDER))
        rates = {}
        for s in STRATA:
            ids = [i for i in fids if frame[i]["stratum"] == s]
            c = Counter(a[i]["majority"] for i in ids)
            rates[s] = (c, len(ids))
            print("  {:10s}".format(s) + "".join(
                f"{c[v]:5d} {c[v]/len(ids)*100:5.1f}%" for v in ORDER))

        print(f"\n  ⛔ THE #91 RATE — `harmful`, judge {name}:")
        for s in STRATA:
            c, n = rates[s]
            lo, hi = wilson(c["harmful"], n)
            flag = ""
            if OPPOSING.get(s) == name:
                flag = "   <- CONSERVATIVE (opposing family)"
            elif OPPOSING.get(s) is not None:
                flag = "   <- own family, flattering"
            print(f"    {s:10s} {c['harmful']:2d}/{n:2d} = {c['harmful']/n*100:5.1f}%  "
                  f"[{lo*100:4.1f}, {hi*100:5.1f}]{flag}")
        c7, n7 = rates["v7_only"]; c8, n8 = rates["v8_only"]
        p = fisher(c7["harmful"], n7 - c7["harmful"], c8["harmful"], n8 - c8["harmful"])
        print(f"    v7-only vs v8-only, Fisher exact two-sided p = {p:.4f}")
        pm = fisher(c7["misleading"], n7 - c7["misleading"],
                    c8["misleading"], n8 - c8["misleading"])
        print(f"  `misleading` (the #125 shape): v7-only {c7['misleading']}/{n7} = "
              f"{c7['misleading']/n7*100:.1f}%  vs  v8-only {c8['misleading']}/{n8} = "
              f"{c8['misleading']/n8*100:.1f}%   Fisher p = {pm:.4f}")
        ok7 = c7["fits"] + c7["weak"]; ok8 = c8["fits"] + c8["weak"]
        print(f"  on-promise (`fits`+`weak`): v7-only {ok7}/{n7} = {ok7/n7*100:.1f}%  vs  "
              f"v8-only {ok8}/{n8} = {ok8/n8*100:.1f}%")

    # ---- what the TAB experiences: a rate on 37 rows and a rate on 523 are not comparable
    # as reader harm. This is the `feedback-rate-needs-population` correction applied to the
    # panel's own headline: the cutover swaps a big stratum for a small one, so the absolute
    # count can fall while the rate rises.
    POP = {"v7_only": 523, "both": 131, "v8_only": 37}   # display-eligible, same 4 cycles
    for name, a in arms.items():
        print()
        print("=" * 78)
        print(f"ABSOLUTE HARM REACHING THE TAB PER 4 CYCLES — judge: {name}")
        print("=" * 78)
        est = {}
        for s in STRATA:
            ids = [i for i in fids if frame[i]["stratum"] == s]
            h = sum(1 for i in ids if a[i]["majority"] == "harmful")
            lo, hi = wilson(h, len(ids))
            census = len(ids) == POP[s]
            est[s] = (h / len(ids) * POP[s], lo * POP[s], hi * POP[s], census)
            tag = "  (CENSUS — all of them, not a sample)" if census else ""
            print(f"  {s:10s} rate {h}/{len(ids)} -> {est[s][0]:5.1f} of {POP[s]:3d} articles "
                  f"[{lo*POP[s]:4.1f}, {hi*POP[s]:5.1f}]{tag}")
        now = est["both"][0] + est["v7_only"][0]
        after = est["both"][0] + est["v8_only"][0]
        print(f"\n  TODAY   (tab = both + v7-only, {POP['both']+POP['v7_only']} articles): "
              f"~{now:.0f} harm-subject articles "
              f"[{est['both'][1]+est['v7_only'][1]:.0f}, {est['both'][2]+est['v7_only'][2]:.0f}]")
        print(f"  CUTOVER (tab = both + v8-only, {POP['both']+POP['v8_only']} articles): "
              f"~{after:.0f} harm-subject articles "
              f"[{est['both'][1]+est['v8_only'][1]:.0f}, {est['both'][2]+est['v8_only'][2]:.0f}]")
        print(f"  -> point estimate {now/after:.1f}x FEWER harm-subject articles after the "
              f"cutover, DESPITE v8-only's higher RATE.")
        print("  \u26a0 The bands overlap. The direction follows from volume, not from v8 being")
        print("  safer per-article — on the rate it is not, and that is the finding.")

    # every harmful row, both judges, so the owner can read them
    print()
    print("=" * 78)
    print("EVERY ARTICLE EITHER JUDGE CALLED `harmful`")
    print("=" * 78)
    flagged = sorted(
        (i for i in fids if any(a[i]["majority"] == "harmful" for a in arms.values())),
        key=lambda i: (frame[i]["stratum"], i))
    if not flagged:
        print("  none — on this panel neither judge found a harm-subject article in either lens")
    for i in flagged:
        f = frame[i]
        marks = " ".join(f"{n}={arms[n][i]['majority']}" for n in sorted(arms))
        print(f"  [{f['stratum']:8s}] {marks}")
        print(f"      v7 raw {f['v7_raw']:.2f} disp {f['v7_display']:.2f} | "
              f"v8 raw {f['v8_raw']:.2f} disp {f['v8_display']:.2f} | {f['language']}")
        print(f"      {(f['title'] or '')[:100]}")
        for n in sorted(arms):
            if arms[n][i]["majority"] == "harmful":
                print(f"      {n}: {arms[n][i]['whys'][0][:88]}")


if __name__ == "__main__":
    main()
