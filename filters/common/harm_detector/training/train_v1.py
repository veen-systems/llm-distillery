#!/usr/bin/env python3
"""Cross-lens harm detector, free arm — trainer + held-out panel evaluation (#156, EXP-037).

⛔ **Read `docs/evidence/2026-09-10-harm-detector/PREREGISTRATION.md` before reading a number
out of this script.** The bar, the decision rule and the predictions were fixed before the
first run, and the primary result is the **panel** count read against the **null arm** — not
the test split, and not zero.

Architecture mirrors `violence_promotion/v1` and `obituary v5` so the artifact contract is the
same: frozen `paraphrase-multilingual-mpnet-base-v2` -> StandardScaler -> MLPClassifier.

⭐ **FIVE SEEDS, A BAND, NOT A POINT.** `H-DET2` (measured 2026-09-10): `early_stopping=True`
lets `random_state` pick the validation split, so obituary recall at 0.85 spanned
0.6599-0.8081 with everything else held fixed. A single-seed detector number is not a result.

Why the panel and not the test split: `H-AP5`. Every `harm_is_subject` positive in this corpus
scores below `weighted_mean_all` 2.7667 and none is at or above 4.0, so they are harm the
ORACLE ALREADY CATCHES. A detector that merely reproduces the oracle's gate scores well on the
test split and is useless for #156. The 137-row `EXP-031` panel is judged, display-eligible,
and shares **0** ids with this corpus.

Usage (b650-gpu, venv-prodparity):
    python3 filters/common/harm_detector/training/train_v1.py \
        --splits datasets/training/human_thriving_v8_scoped \
        --panel-content datasets/panel/panel_content.jsonl \
        --panel-judges docs/evidence/2026-09-08-thriving-harm-panel \
        --out docs/evidence/2026-09-10-harm-detector/report.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

EMBEDDER = "paraphrase-multilingual-mpnet-base-v2"
HIDDEN = (256, 128)
POSITIVE_VERDICT = "harm_is_subject"
#: The full `scope_verdict` vocabulary as measured on labels_v84_merged.jsonl (6,586 rows).
#: Adding a value here is a decision about the labelling function, not a config tweak.
KNOWN_VERDICTS = frozenset({
    "harm_is_subject", "in_scope", "out_of_scope", "response_to_harm", "no_person_benefits",
})
VAL_SPECIFICITY_TARGET = 0.98      # ADR-023: specificity first. Where deployed filters sit.
N_SEEDS = 5                        # H-DET2. Not negotiable down to 1.


def load_split(path: Path):
    """Rows -> (texts, y). Raises on a missing `scope_verdict`; never defaults it.

    `oracle_meta` is verbatim and heterogeneous (`runs` is a list on 6,130 rows and an int on
    456). `scope_verdict` is the only non-dimension key measured present on all 6,586 — so it
    is the only one this reads, and a missing one is a corpus defect, not a negative label.
    """
    texts, y = [], []
    for lineno, line in enumerate(path.open(encoding="utf-8"), 1):
        if not line.strip():
            continue
        r = json.loads(line)
        meta = r.get("oracle_meta") or {}
        verdict = meta.get("scope_verdict")
        if verdict is None:
            raise ValueError(
                f"{path}:{lineno} has no oracle_meta.scope_verdict — this split predates #155. "
                f"Rebuild with training/prepare_data.py; do NOT treat absence as a negative."
            )
        # ⛔ ENUMERATED, not "anything else is a negative". The unbounded-negative form is the
        # denylist shape this repo removed from the DeepSeek guard on 2026-09-10: a partial
        # rename upstream would shrink the positive class SILENTLY, and only a TOTAL rename
        # crashes (MLPClassifier needs two classes). An unknown verdict is a corpus change.
        if verdict not in KNOWN_VERDICTS:
            raise ValueError(
                f"{path}:{lineno} has scope_verdict {verdict!r}, which is not in "
                f"{sorted(KNOWN_VERDICTS)}. The vocabulary changed upstream — decide what the "
                f"new value means before training on it; do not let it become a negative."
            )
        texts.append(f"{r.get('title') or ''} {r.get('content') or ''}".strip())
        y.append(1 if verdict == POSITIVE_VERDICT else 0)
    return texts, np.array(y)


def load_panel(content_path: Path, judges_dir: Path):
    """The held-out arbiter: 137 judged production rows, 0 of them in the training corpus."""
    rows = [json.loads(l) for l in content_path.open(encoding="utf-8") if l.strip()]
    gem = {r["id"] for r in json.load((judges_dir / "judge_gemini_k1.json").open())
           if r["majority"] == "harmful"}
    dsk = {r["id"] for r in json.load((judges_dir / "judge_deepseek_k3.json").open())
           if r["majority"] == "harmful"}
    both = gem & dsk
    if not both <= gem:                              # H-AP3's nesting, re-asserted here
        raise ValueError("DeepSeek harmful is not a subset of Gemini harmful — H-AP3 changed")
    texts = [f"{r.get('title') or ''} {r.get('content') or ''}".strip() for r in rows]
    ids = [r["id"] for r in rows]
    return ids, texts, gem, both


def spec_recall(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    return float(spec), float(rec), int(tp), int(fp), int(fn), int(tn)


def pick_threshold(p_val, y_val, target=VAL_SPECIFICITY_TARGET):
    """Lowest threshold on the VAL split reaching `target` specificity.

    Lowest, not highest: among thresholds that satisfy the specificity constraint we want the
    most sensitive one. Returns 1.01 (fires on nothing) when the constraint is unreachable —
    which is itself a result and must be reported, not silently clamped.
    """
    for t in np.arange(0.01, 1.0001, 0.005):
        spec, _, _, _, _, _ = spec_recall(y_val, (p_val >= t).astype(int))
        if spec >= target:
            return float(t)
    return 1.01


SWEEP = [0.30, 0.40, 0.50, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.99]


def sweep_arm(p_te, y_te, p_pan, ids, gem, both):
    """The pre-registration's escape hatch, honoured.

    It said: if the chosen threshold flags <2% or >40% of the panel, the catch count is a
    property of the threshold rather than of the detector, and the whole sweep must be
    reported instead of a headline. Three of five seeds land at or under 2%, so this runs.
    """
    out = []
    for t in SWEEP:
        te_spec, te_rec, *_ = spec_recall(y_te, (p_te >= t).astype(int))
        flagged = {i for i, p in zip(ids, p_pan) if p >= t}
        out.append({
            "threshold": t,
            "test_specificity": round(te_spec, 4),
            "test_recall": round(te_rec, 4),
            "panel_flagged": len(flagged),
            "panel_flag_rate": round(len(flagged) / len(ids), 4),
            "caught_both9": len(flagged & both),
            "caught_gem32": len(flagged & gem),
            # Of everything the detector flags on the panel, how much a judge also called
            # harmful. The firing-rate control, expressed per flag rather than per row.
            "panel_precision_vs_gem32": round(len(flagged & gem) / len(flagged), 4) if flagged else None,
        })
    return out


def run_arm(X_tr, y_tr, X_val, y_val, X_te, y_te, X_pan, ids, gem, both, seed):
    scaler = StandardScaler().fit(X_tr)
    clf = MLPClassifier(hidden_layer_sizes=HIDDEN, max_iter=400, early_stopping=True,
                        n_iter_no_change=15, random_state=seed)
    clf.fit(scaler.transform(X_tr), y_tr)

    p_val = clf.predict_proba(scaler.transform(X_val))[:, 1]
    p_te = clf.predict_proba(scaler.transform(X_te))[:, 1]
    p_pan = clf.predict_proba(scaler.transform(X_pan))[:, 1]

    t = pick_threshold(p_val, y_val)
    te_spec, te_rec, *_ = spec_recall(y_te, (p_te >= t).astype(int))

    flagged = {i for i, p in zip(ids, p_pan) if p >= t}
    unflagged_by_judges = [i for i in ids if i not in gem]
    panel_spec = sum(1 for i in unflagged_by_judges if i not in flagged) / len(unflagged_by_judges)

    return {
        "seed": seed,
        # ⚠️ The panel is STRATIFIED (60 v7_only / 40 both / 37 v8_only) and production is
        # not (523 / 131 / 37). A flag RATE read off the panel carries the panel's design
        # weighting and is NOT a production blocking rate. Per-row probabilities are dumped
        # so the rate can be re-weighted per stratum without retraining.
        "panel_probs": {i: round(float(p), 6) for i, p in zip(ids, p_pan)},
        "sweep": sweep_arm(p_te, y_te, p_pan, ids, gem, both),
        "threshold": round(t, 4),
        "val_spec_target_met": t <= 1.0,
        "test_specificity": round(te_spec, 4),
        "test_recall": round(te_rec, 4),
        "panel_flag_rate": round(len(flagged) / len(ids), 4),
        "panel_caught_both9": len(flagged & both),
        "panel_caught_gem32": len(flagged & gem),
        "panel_specificity_on_105": round(panel_spec, 4),
    }


def band(rows, key):
    v = [r[key] for r in rows]
    bad = [type(x).__name__ for x in v if not isinstance(x, (int, float)) or isinstance(x, bool)]
    if bad:
        # An ALLOWLIST of scalar types, not a denylist of list. The first version named `list`
        # and fell straight through on `panel_probs`, a DICT on the same rows — min()/mean()
        # over dicts, silently. Same shape as the DeepSeek denylist, same day.
        raise TypeError(f"band() called on non-scalar key {key!r} (saw {sorted(set(bad))}) — "
                        f"bands are for numbers")
    return {"min": min(v), "mean": round(float(np.mean(v)), 4), "max": max(v)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", required=True)
    ap.add_argument("--panel-content", required=True)
    ap.add_argument("--panel-judges", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    sp = Path(args.splits)
    tr_txt, y_tr = load_split(sp / "train.jsonl")
    va_txt, y_va = load_split(sp / "val.jsonl")
    te_txt, y_te = load_split(sp / "test.jsonl")
    ids, pan_txt, gem, both = load_panel(Path(args.panel_content), Path(args.panel_judges))

    print(f"train {len(tr_txt)} (pos {int(y_tr.sum())}) | val {len(va_txt)} (pos {int(y_va.sum())}) "
          f"| test {len(te_txt)} (pos {int(y_te.sum())}) | panel {len(pan_txt)} "
          f"(gemini-harmful {len(gem)}, both-harmful {len(both)})")

    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer(EMBEDDER, device=args.device)
    print(f"embedding {len(tr_txt)+len(va_txt)+len(te_txt)+len(pan_txt)} texts on {args.device} ...")
    enc = lambda t: np.asarray(embedder.encode(t, batch_size=64, show_progress_bar=False))
    X_tr, X_va, X_te, X_pan = enc(tr_txt), enc(va_txt), enc(te_txt), enc(pan_txt)

    real, null = [], []
    for seed in range(N_SEEDS):
        real.append(run_arm(X_tr, y_tr, X_va, y_va, X_te, y_te, X_pan, ids, gem, both, seed))
        print("  real", real[-1])
        # NULL ARM: same everything, labels shuffled. The primary is read against THIS,
        # not against zero — a detector with no signal still catches some of 9 at any
        # firing rate.
        rng = np.random.default_rng(seed)
        null.append(run_arm(X_tr, rng.permutation(y_tr), X_va, rng.permutation(y_va),
                            X_te, y_te, X_pan, ids, gem, both, seed))
        print("  null", null[-1])

    # ⛔ An unreachable val constraint must be LOUD. `pick_threshold` returns the 1.01 sentinel,
    # which yields test_specificity 1.0 / recall 0.0 / flag_rate 0 — indistinguishable from "an
    # unusually conservative seed" — and `band()` then averages 1.01 in with real thresholds.
    # The flag existed and nothing read it.
    unreachable = [r["seed"] for r in real + null if not r["val_spec_target_met"]]
    if unreachable:
        raise RuntimeError(
            f"seeds {unreachable} could not reach val specificity {VAL_SPECIFICITY_TARGET} at "
            f"any threshold. Their metrics are sentinels, not measurements — fix the target or "
            f"the data before reading this report."
        )

    keys = ["test_specificity", "test_recall", "panel_flag_rate", "panel_caught_both9",
            "panel_caught_gem32", "panel_specificity_on_105", "threshold"]
    report = {
        "experiment": "EXP-037",
        "issue": "llm-distillery#156",
        "prereg": "docs/evidence/2026-09-10-harm-detector/PREREGISTRATION.md",
        "embedder": EMBEDDER,
        "hidden": list(HIDDEN),
        "n_seeds": N_SEEDS,
        "val_specificity_target": VAL_SPECIFICITY_TARGET,
        "counts": {"train": len(tr_txt), "train_pos": int(y_tr.sum()),
                   "val": len(va_txt), "val_pos": int(y_va.sum()),
                   "test": len(te_txt), "test_pos": int(y_te.sum()),
                   "panel": len(ids), "panel_gemini_harmful": len(gem),
                   "panel_both_harmful": len(both)},
        "real_per_seed": real,
        "null_per_seed": null,
        "real_bands": {k: band(real, k) for k in keys},
        "null_bands": {k: band(null, k) for k in keys},
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {args.out}")
    print("REAL bands:", json.dumps(report["real_bands"], indent=1))
    print("NULL bands:", json.dumps(report["null_bands"], indent=1))


if __name__ == "__main__":
    main()
