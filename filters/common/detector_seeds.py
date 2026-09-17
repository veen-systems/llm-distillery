"""One home for the detector seed rule (llm-distillery#158).

⛔ **`early_stopping=True` makes `random_state` choose the internal validation split**, so a
detector head trained with everything else held fixed is one draw from a distribution, not a
property of the model. Measured 2026-09-10 (`EXP-033`, `EXP-034`): obituary heldout recall at the
live **0.85** op-point ranges **0.6599–0.8081** across five seeds — a **0.148** spread, and
**0.285** at 0.95. `EXP-034` retrained v3/v4/v5 and got **three different orderings** across five
seeds: every version wins under some seed.

⭐ **The rule this module exists to make unavoidable: a detector metric is published as a BAND over
`SEED_SET`, never as a point.** `scripts/verification/check_detector_metric_bands.py` enforces it
on the artifact, and `tests/unit/test_detector_metric_bands.py` enforces that the trainers call
`oof_by_seed` rather than rolling their own single-seed loop.

⚠️ **This does NOT say the shipped models are bad**, and it is not a reason to replace one. A band
is a statement about the protocol that produced a head, not about the head that is serving.
"""

from __future__ import annotations

import numpy as np

#: `EXP-033`'s set. ⛔ Changing it changes what every future band means, so it is a decision about
#: the reporting rule, not a tuning knob — and a band computed over a DIFFERENT set is not
#: comparable to one computed over this one. Record the set beside the band, always.
SEED_SET = (42, 7, 13, 101, 2026)

#: Which seed's refit is saved as the deployed artifact. ⛔ Kept at 42 deliberately: #158 is a
#: REPORTING defect, and changing which head ships would silently make the fix a model change.
#: The artifact's own seed is recorded so "which draw is serving?" has an answer in the file.
ARTIFACT_SEED = 42

HIDDEN = (256, 128)
MAX_ITER = 400
N_ITER_NO_CHANGE = 15
N_SPLITS = 5


def make_mlp(seed: int):
    """The head every detector here trains. `seed` is required — there is no default.

    ⛔ A default would be the defect: `SEED = 42` as a module constant is exactly what #158 is
    about, and a caller that forgets the argument should fail loudly rather than quietly pick 42.
    """
    from sklearn.neural_network import MLPClassifier

    return MLPClassifier(hidden_layer_sizes=HIDDEN, max_iter=MAX_ITER,
                         early_stopping=True, n_iter_no_change=N_ITER_NO_CHANGE,
                         random_state=seed)


def oof_by_seed(X, y, seeds=SEED_SET, n_splits: int = N_SPLITS, verbose: bool = True):
    """{seed: out-of-fold probability vector} — the whole band in one pass over the embeddings.

    The fold split is seeded too (`StratifiedKFold(random_state=seed)`), because both halves of
    the draw are what #158 measured: `EXP-033` varied `random_state` on the head and the fold
    split together, and the 0.6599–0.8081 spread is that pair's.
    """
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler

    y = np.asarray(y)
    out = {}
    for seed in seeds:
        oof = np.zeros(len(y), dtype=float)
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        for fold, (tr, te) in enumerate(skf.split(X, y)):
            sc = StandardScaler().fit(X[tr])
            clf = make_mlp(seed).fit(sc.transform(X[tr]), y[tr])
            oof[te] = clf.predict_proba(sc.transform(X[te]))[:, 1]
            if verbose:
                print(f"  seed {seed} fold {fold}: train={len(tr)} test={len(te)}")
        out[seed] = oof
    return out


def band(per_seed: dict) -> dict:
    """{seed: value} -> the published band. ⛔ Carries its OWN seeds; a band without them is a
    number whose population is unstated, which is the shape this repo keeps getting wrong."""
    vals = [float(v) for v in per_seed.values()]
    if len(vals) < 2:
        raise ValueError(
            f"band() needs at least two seeds, got {len(vals)} — a one-seed 'band' is the "
            f"single-seed defect wearing the fix's name (llm-distillery#158)")
    return {
        "min": round(min(vals), 4),
        "median": round(float(np.median(vals)), 4),
        "max": round(max(vals), 4),
        "spread": round(max(vals) - min(vals), 4),
        "seeds": [int(s) for s in per_seed],
        "per_seed": {str(s): round(float(v), 4) for s, v in per_seed.items()},
    }


def metric_bands(oofs: dict, y, metric_fns: dict, thresholds) -> dict:
    """`{"<name>_at_<th>_band": band}` for every (metric, threshold) pair.

    `metric_fns` maps a name to `f(y_true, y_pred) -> float`. Kept caller-supplied because the two
    detectors publish different headline thresholds (obituary's live op-point is 0.85, the
    audit-baseline tables are at 0.95) and a hardcoded list here would quietly drop one.
    """
    y = np.asarray(y)
    out = {}
    for th in thresholds:
        for name, fn in metric_fns.items():
            per_seed = {s: float(fn(y, (oof >= th).astype(int))) for s, oof in oofs.items()}
            out[f"oof_{name}_at_{th}_band"] = band(per_seed)
    return out
