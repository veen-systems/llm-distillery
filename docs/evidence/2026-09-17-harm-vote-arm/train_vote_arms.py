#!/usr/bin/env python3
"""The per-run-vote arm of the cross-lens harm detector (#156, EXP-039).

⛔ **Read `docs/evidence/2026-09-17-harm-vote-arm/PREREGISTRATION.md` before reading a number out
of this script.** The three arms, the primary (paired B − A on the 9), the decision rule and the
predictions were all fixed before the first run.

⭐ **The architecture is IMPORTED from `filters/common/harm_detector/training/train_v1.py`, not
copied.** `run_arm`, `pick_threshold`, `band`, the embedder name, the hidden sizes, the seed count
and the val specificity target are that module's objects. One variable changes across arms — the
definition of the positive class — and one across this script and `EXP-037`: nothing else. A copy
would drift, and this repo has already shipped a defect that rode a hand copy between two trees
(`bb5a52d`).

⚠️ **Only the PANEL numbers are comparable across arms.** Each arm's test split carries its own
labels, so its test recall/specificity describe agreement with that arm's own labelling function.

Usage (b650-gpu, venv-prodparity):
    python3 docs/evidence/2026-09-17-harm-vote-arm/train_vote_arms.py \
        --splits datasets/training/human_thriving_v8_scoped \
        --panel-content ~/llm-distillery/datasets/panel/panel_content.jsonl \
        --panel-judges docs/evidence/2026-09-08-thriving-harm-panel \
        --out docs/evidence/2026-09-17-harm-vote-arm/report.json
"""

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
TRAIN_V1 = REPO / "filters/common/harm_detector/training/train_v1.py"


def _import_train_v1():
    """The shipped EXP-037 trainer, loaded by PATH so the report can name the file it used."""
    spec = importlib.util.spec_from_file_location("harm_train_v1", TRAIN_V1)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T = _import_train_v1()

#: The three positive-class definitions. ⛔ A new arm is a decision about the labelling function,
#: not a config tweak — it belongs in a pre-registration first.
ARMS = ("final", "vote_union", "vote_only")


def load_rows(path: Path):
    """Rows -> (texts, verdicts, harm_vote_counts, n_votes).

    Reads `scope_verdicts_per_run`, which is the ONLY per-run field measured present on all
    6,586 rows: `runs` is a list on 6,130 and an int on 456, and `weighted_mean_major` is absent
    on those 456. Same enumerated-vocabulary rule as `train_v1.load_split` — an unknown verdict
    raises rather than becoming a negative, in the per-run list too.
    """
    texts, verdicts, harm_votes, n_votes = [], [], [], []
    for lineno, line in enumerate(path.open(encoding="utf-8"), 1):
        if not line.strip():
            continue
        r = json.loads(line)
        meta = r.get("oracle_meta") or {}
        verdict = meta.get("scope_verdict")
        if verdict is None:
            raise ValueError(f"{path}:{lineno} has no oracle_meta.scope_verdict — split predates #155")
        if verdict not in T.KNOWN_VERDICTS:
            raise ValueError(f"{path}:{lineno} scope_verdict {verdict!r} outside {sorted(T.KNOWN_VERDICTS)}")
        per_run = meta.get("scope_verdicts_per_run")
        if not isinstance(per_run, list) or not per_run:
            # ⛔ Not a negative and not a zero. This arm IS the per-run votes; a row that cannot
            # supply them is a corpus defect, and returning 0 here would silently make every
            # such row a negative in arms B and C — the exact shape #156's own guards forbid.
            raise ValueError(
                f"{path}:{lineno} has scope_verdicts_per_run {per_run!r} (want a non-empty list). "
                f"Measured present as a list on 6,586/6,586 rows on 2026-09-17; if that changed, "
                f"decide what the new shape means before training on it."
            )
        for v in per_run:
            if v not in T.KNOWN_VERDICTS:
                raise ValueError(f"{path}:{lineno} per-run verdict {v!r} outside the known vocabulary")
        texts.append(f"{r.get('title') or ''} {r.get('content') or ''}".strip())
        verdicts.append(verdict)
        harm_votes.append(sum(1 for v in per_run if v == T.POSITIVE_VERDICT))
        n_votes.append(len(per_run))
    return texts, verdicts, np.array(harm_votes), np.array(n_votes)


def labels_for(arm: str, verdicts, harm_votes):
    """(y, keep_mask) for one arm. `keep_mask` drops rows the arm removes from the corpus."""
    final = np.array([1 if v == T.POSITIVE_VERDICT else 0 for v in verdicts])
    minority = ((harm_votes >= 1) & (final == 0)).astype(int)
    if arm == "final":
        return final, np.ones(len(final), dtype=bool)
    if arm == "vote_union":
        return ((final == 1) | (harm_votes >= 1)).astype(int), np.ones(len(final), dtype=bool)
    if arm == "vote_only":
        # ⛔ REMOVED, not relabelled negative. Calling a row the oracle finally labelled
        # `harm_is_subject` a negative would train the detector against the very class it is
        # for; the arm's question is whether the MINORITY-vote rows carry the shape on their own.
        return minority, (final == 0)
    raise ValueError(f"unknown arm {arm!r}")


def topk_catch(p_pan, ids, both, k):
    """RATE-MATCHED control: the k highest-scoring panel rows, how many are in the 9.

    Arm B has 13.4% more positives than A, so it may fire more and catch more by volume. Matching
    on k removes the firing rate from the comparison. Ties are broken by probability order alone,
    which is the same rule for every arm.
    """
    order = np.argsort(-np.asarray(p_pan))[:k]
    return len({ids[i] for i in order} & both)


def provenance(device: str) -> dict:
    """What produced this report, recorded so a number can be traced to a tree and a box.

    ⛔ This script may run from a checkout that is AHEAD of the box's HEAD (it is copied there as
    an untracked evidence script). Hashing both files defeats that: `repo_head` names the tree the
    ARCHITECTURE came from, and the two digests name the exact bytes that ran.
    """
    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    try:
        head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception as exc:                      # a box without git is a provenance gap, not a crash
        head = f"UNAVAILABLE: {exc}"
    return {
        "repo_head": head,
        "script_sha256": sha(Path(__file__).resolve()),
        "train_v1_sha256": sha(TRAIN_V1),
        "device": device,
        "host": subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", required=True)
    ap.add_argument("--panel-content", required=True)
    ap.add_argument("--panel-judges", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    sp = Path(args.splits)
    rows = {name: load_rows(sp / f"{name}.jsonl") for name in ("train", "val", "test")}

    # ⭐ LOADER CONTROL (prereg control 4): the shipped loader is the reference object. If this
    # script's `final` labels or texts differ from `train_v1.load_split`'s by one row, every
    # cross-arm comparison below is against a different arm A than EXP-037 ran.
    for name, (texts, verdicts, harm_votes, _) in rows.items():
        ref_texts, ref_y = T.load_split(sp / f"{name}.jsonl")
        mine, _ = labels_for("final", verdicts, harm_votes)
        if ref_texts != texts:
            raise RuntimeError(f"{name}: texts differ from train_v1.load_split — arms are not comparable")
        if not np.array_equal(ref_y, mine):
            raise RuntimeError(f"{name}: `final` labels differ from train_v1.load_split")
    print("loader control: texts and `final` labels identical to train_v1.load_split on all splits")

    ids, pan_txt, gem, both = T.load_panel(Path(args.panel_content), Path(args.panel_judges))

    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer(T.EMBEDDER, device=args.device)
    enc = lambda t: np.asarray(embedder.encode(t, batch_size=64, show_progress_bar=False))
    # ⭐ Embedded ONCE. Every arm indexes into these matrices, so no arm can differ by an
    # embedding — and on a box whose GPU changed today that is the difference between a label
    # finding and a hardware finding (EXP-038).
    print(f"embedding {sum(len(rows[n][0]) for n in rows) + len(pan_txt)} texts on {args.device} ...")
    X = {name: enc(rows[name][0]) for name in rows}
    X_pan = enc(pan_txt)

    results = {}
    for arm in ARMS:
        y, keep = {}, {}
        for name, (_, verdicts, harm_votes, _) in rows.items():
            y[name], keep[name] = labels_for(arm, verdicts, harm_votes)
        Xa = {n: X[n][keep[n]] for n in rows}
        ya = {n: y[n][keep[n]] for n in rows}
        print(f"\n=== arm {arm}: "
              + " | ".join(f"{n} {len(ya[n])} (pos {int(ya[n].sum())})" for n in ("train", "val", "test")))

        real, null = [], []
        for seed in range(T.N_SEEDS):
            real.append(T.run_arm(Xa["train"], ya["train"], Xa["val"], ya["val"],
                                  Xa["test"], ya["test"], X_pan, ids, gem, both, seed))
            rng = np.random.default_rng(seed)
            null.append(T.run_arm(Xa["train"], rng.permutation(ya["train"]),
                                  Xa["val"], rng.permutation(ya["val"]),
                                  Xa["test"], ya["test"], X_pan, ids, gem, both, seed))
            print(f"  seed {seed}: real both9={real[-1]['panel_caught_both9']} "
                  f"flag={real[-1]['panel_flag_rate']} t={real[-1]['threshold']} "
                  f"| null both9={null[-1]['panel_caught_both9']} flag={null[-1]['panel_flag_rate']}")

        unreachable = [r["seed"] for r in real + null if not r["val_spec_target_met"]]
        if unreachable:
            raise RuntimeError(f"arm {arm}: seeds {unreachable} never reached val specificity "
                               f"{T.VAL_SPECIFICITY_TARGET} — those metrics are sentinels")

        keys = ["test_specificity", "test_recall", "panel_flag_rate", "panel_caught_both9",
                "panel_caught_gem32", "panel_specificity_on_105", "threshold"]
        results[arm] = {
            "counts": {f"{n}": int(len(ya[n])) for n in ("train", "val", "test")}
                      | {f"{n}_pos": int(ya[n].sum()) for n in ("train", "val", "test")},
            "real_per_seed": real,
            "null_per_seed": null,
            "real_bands": {k: T.band(real, k) for k in keys},
            "null_bands": {k: T.band(null, k) for k in keys},
        }

    # PRIMARY: paired per seed. Band overlap is the weaker instrument here — the arms share
    # embeddings, seeds and panel, so the difference is measurable row by row.
    a = results["final"]["real_per_seed"]
    paired = {}
    for arm in ("vote_union", "vote_only"):
        b = results[arm]["real_per_seed"]
        d9 = [b[i]["panel_caught_both9"] - a[i]["panel_caught_both9"] for i in range(T.N_SEEDS)]
        d32 = [b[i]["panel_caught_gem32"] - a[i]["panel_caught_gem32"] for i in range(T.N_SEEDS)]
        matched = [topk_catch(list(b[i]["panel_probs"].values()), list(b[i]["panel_probs"].keys()),
                              both, max(1, round(a[i]["panel_flag_rate"] * len(ids))))
                   for i in range(T.N_SEEDS)]
        paired[arm] = {
            "delta_both9_per_seed": d9,
            "delta_both9_mean": round(float(np.mean(d9)), 4),
            "delta_gem32_per_seed": d32,
            "delta_gem32_mean": round(float(np.mean(d32)), 4),
            "rate_matched_topk_catch_both9": matched,
            "rate_matched_topk_catch_both9_mean": round(float(np.mean(matched)), 4),
            "arm_a_topk_per_seed": [max(1, round(a[i]["panel_flag_rate"] * len(ids)))
                                    for i in range(T.N_SEEDS)],
            "arm_a_catch_both9_per_seed": [a[i]["panel_caught_both9"] for i in range(T.N_SEEDS)],
        }

    report = {
        "experiment": "EXP-039",
        "issue": "llm-distillery#156",
        "prereg": "docs/evidence/2026-09-17-harm-vote-arm/PREREGISTRATION.md",
        "architecture_from": str(TRAIN_V1.relative_to(REPO)),
        "embedder": T.EMBEDDER,
        "hidden": list(T.HIDDEN),
        "n_seeds": T.N_SEEDS,
        "provenance": provenance(args.device),
        "val_specificity_target": T.VAL_SPECIFICITY_TARGET,
        "panel": {"n": len(ids), "gemini_harmful": len(gem), "both_harmful": len(both)},
        "arms": results,
        "paired_vs_final": paired,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {args.out}")
    for arm in ARMS:
        print(f"{arm:11s} real both9 {results[arm]['real_bands']['panel_caught_both9']} "
              f"| null both9 {results[arm]['null_bands']['panel_caught_both9']} "
              f"| real flag {results[arm]['real_bands']['panel_flag_rate']} "
              f"| null flag {results[arm]['null_bands']['panel_flag_rate']}")
    print("PAIRED:", json.dumps(paired, indent=1))


if __name__ == "__main__":
    main()
