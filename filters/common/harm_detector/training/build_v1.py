#!/usr/bin/env python3
"""Build the shippable harm detector v1 — a 5-seed ENSEMBLE, stamp-only (#156).

⛔ **This ships a SCORE, never a verdict.** ADR-022: stamp always, decide once. The artifact
writes a probability in [0,1] onto every article and **no threshold is baked in**. Each lens's
gate is a later config flip against a number that is already on the row — which is why no
threshold had to be guessed today, and why choosing one now would be the mistake.

⭐ **Why an ensemble and not "the best seed".** `H-DET2` (measured 2026-09-10): with everything
else fixed, `early_stopping=True` lets `random_state` pick the internal validation split, so a
detector's headline metric swings wildly by seed — obituary recall at 0.85 spanned 0.6599-0.8081,
and this detector's own catch count on the panel spanned 0-3 across five seeds. **Picking the seed
that scores best is seed-shopping and ships a lottery ticket.** Averaging the five removes the
choice entirely, and it is free at inference: one embedding pass feeds five very small MLPs.

Companion experiment (the numbers, the null arm, the refuted predictions): `EXP-037`,
`docs/evidence/2026-09-10-harm-detector/`.

Usage (b650-gpu, venv-prodparity):
    python3 filters/common/harm_detector/training/build_v1.py \
        --splits datasets/training/human_thriving_v8_scoped \
        --panel-content datasets/panel/panel_content.jsonl \
        --panel-judges docs/evidence/2026-09-08-thriving-harm-panel \
        --out-dir filters/common/harm_detector/v1/models \
        --report filters/common/harm_detector/v1/calibration_report.json
"""

import argparse
import json
import pickle
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_v1 import (                      # one definition, not a tidied copy  # noqa: E402
    EMBEDDER, HIDDEN, N_SEEDS, POSITIVE_VERDICT, load_panel, load_split, spec_recall, sweep_arm,
)


def git_commit(repo: Path) -> str:
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("not a git checkout — an artifact that cannot name its commit "
                           "cannot be traced back to the code that made it")
    dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"],
                           capture_output=True, text=True).stdout.strip()
    return r.stdout.strip() + ("-dirty" if dirty else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", required=True)
    ap.add_argument("--panel-content", required=True)
    ap.add_argument("--panel-judges", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[4]
    commit = git_commit(repo)

    sp = Path(args.splits)
    tr_txt, y_tr = load_split(sp / "train.jsonl")
    va_txt, y_va = load_split(sp / "val.jsonl")
    te_txt, y_te = load_split(sp / "test.jsonl")
    ids, pan_txt, gem, both = load_panel(Path(args.panel_content), Path(args.panel_judges))
    print(f"train {len(tr_txt)} (pos {int(y_tr.sum())}) | val {len(va_txt)} | test {len(te_txt)} "
          f"| panel {len(ids)} (gem {len(gem)}, both {len(both)})")

    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer(EMBEDDER, device=args.device)
    enc = lambda t: np.asarray(embedder.encode(t, batch_size=64, show_progress_bar=False))
    X_tr, X_va, X_te, X_pan = enc(tr_txt), enc(va_txt), enc(te_txt), enc(pan_txt)

    scaler = StandardScaler().fit(X_tr)
    Z_tr, Z_va, Z_te, Z_pan = (scaler.transform(x) for x in (X_tr, X_va, X_te, X_pan))

    clfs, per_seed = [], []
    P_te, P_pan, P_va = [], [], []
    for seed in range(N_SEEDS):
        clf = MLPClassifier(hidden_layer_sizes=HIDDEN, max_iter=400, early_stopping=True,
                            n_iter_no_change=15, random_state=seed).fit(Z_tr, y_tr)
        clfs.append(clf)
        p_te = clf.predict_proba(Z_te)[:, 1]
        p_pan = clf.predict_proba(Z_pan)[:, 1]
        P_te.append(p_te); P_pan.append(p_pan); P_va.append(clf.predict_proba(Z_va)[:, 1])
        per_seed.append({"seed": seed, "sweep": sweep_arm(p_te, y_te, p_pan, ids, gem, both)})
        print(f"  seed {seed} trained")

    # The shipped score: the mean of the five. Not a vote — the stamp is continuous.
    ens_te, ens_pan, ens_va = (np.mean(np.vstack(P), axis=0) for P in (P_te, P_pan, P_va))
    ens_sweep = sweep_arm(ens_te, y_te, ens_pan, ids, gem, both)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "scaler.pkl").open("wb") as f:
        pickle.dump(scaler, f)
    for seed, clf in enumerate(clfs):
        with (out / f"mlp_classifier_seed{seed}.pkl").open("wb") as f:
            pickle.dump(clf, f)

    config = {
        "version": "v1",
        "detector": "harm_is_subject",
        "stamp_only": True,
        "threshold": None,                 # deliberate: the gate is a per-lens config flip
        "ensemble_seeds": list(range(N_SEEDS)),
        "embedder": EMBEDDER,
        "hidden_layer_sizes": list(HIDDEN),
        "positive_label": POSITIVE_VERDICT,
        "trained_from": str(sp),
        "counts": {"train": len(tr_txt), "train_pos": int(y_tr.sum()),
                   "val": len(va_txt), "val_pos": int(y_va.sum()),
                   "test": len(te_txt), "test_pos": int(y_te.sum())},
        "sklearn_version": sklearn.__version__,
        "commit": commit,
        "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experiment": "EXP-037",
        "issue": "llm-distillery#156",
    }
    (out / "training_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    report = {
        **config,
        "ensemble_sweep": ens_sweep,
        "per_seed_sweep": per_seed,
        "panel_probs_ensemble": {i: round(float(p), 6) for i, p in zip(ids, ens_pan)},
        "note": ("The stamp is the ensemble probability. No threshold is shipped. "
                 "Per-lens gating is a config flip against a stamped number (ADR-022). "
                 "The panel is uplifting v7 / human_thriving v8 display-eligible rows only and "
                 "says nothing about solutions, belonging, nature_recovery or cultural_discovery."),
    }
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {args.out_dir} and {args.report}\ncommit {commit}")
    print("\nENSEMBLE sweep (test spec/recall, panel catches):")
    for r in ens_sweep:
        print(f"  thr {r['threshold']:.2f}  flagged {r['panel_flagged']:3d} "
              f"({r['panel_flag_rate']*100:5.2f}%)  of9 {r['caught_both9']}  of32 {r['caught_gem32']}  "
              f"te_spec {r['test_specificity']:.4f}  te_rec {r['test_recall']:.4f}")


if __name__ == "__main__":
    main()
