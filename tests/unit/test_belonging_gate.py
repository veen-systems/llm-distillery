"""The belonging retrain gate's rule (docs/evidence/2026-10-03-belonging-heldout/gate.py, GATE.md § Pass rule v2),
on synthetic rows: no judge files or GPU needed. The same controls run on real production raws via
`gate.py controls`; these pin the mechanics so a later edit cannot quietly change what passes."""
import importlib
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "docs" / "evidence" / "2026-10-03-belonging-heldout"
sys.path.insert(0, str(HERE))
gate = importlib.import_module("gate")


def _lab(n_pos=44, negs=(("near", "gemini_out_sample", 40), ("hi", "gemini_out_sample", 30), ("hi", "gemini_in", 10))):
    lab = {f"p{j}": dict(label="pos", band="hi", pick="gemini_in", weight=1.0) for j in range(n_pos)}
    for band, pick, n in negs:
        for j in range(n):
            lab[f"n_{band}_{pick}_{j}"] = dict(label="neg", band=band, pick=pick, weight=3.0 if pick != "gemini_in" else 1.0)
    lab["d0"] = dict(label="disputed", band="hi", pick="gemini_in", weight=1.0)
    return lab


def _scores(lab, pos_score, neg_score, stage="stage2"):
    return {i: dict(stage_used=stage, weighted_average=pos_score(i) if x["label"] == "pos" else neg_score(i))
            for i, x in lab.items()}


def _v1(lab):
    # v1: positives spread 4.1..8.4, negatives: one third score in (5.0), the rest out (1.0)
    return _scores(lab, lambda i: 4.1 + 0.1 * int(i[1:]), lambda i: 5.0 if i[-1] in "036" else 1.0)


def test_stage1_low_is_out_whatever_its_score():
    assert not gate.is_in(dict(stage_used="stage1_low", weighted_average=9.9), 4.0)
    assert gate.is_in(dict(stage_used="stage2", weighted_average=4.0), 4.0)


def test_t_star_is_the_highest_threshold_keeping_k():
    lab = _lab()
    v1 = _v1(lab)
    pos = [i for i in lab if lab[i]["label"] == "pos"]
    assert gate.t_star(v1, pos, 1) == pytest.approx(8.4)
    assert gate.t_star(v1, pos, 44) == pytest.approx(4.1)
    assert sum(gate.is_in(v1[i], gate.t_star(v1, pos, 31)) for i in pos) == 31
    assert gate.t_star(v1, pos, 0) == math.inf


def test_t_star_raises_when_v1_cannot_match():
    lab = _lab()
    v1 = _scores(lab, lambda i: 5.0, lambda i: 1.0, stage="stage1_low")
    with pytest.raises(SystemExit):
        gate.t_star(v1, [i for i in lab if lab[i]["label"] == "pos"], 10)


def test_v1_against_itself_fails():
    lab = _lab()
    v1 = _v1(lab)
    r = gate.decide(lab, v1, v1, 4.0, nboot=200)
    assert not r["passed"] and r["delta"] <= 0


def test_a_higher_op_point_alone_cannot_pass():
    """The 2026-10-03 refutation: v1 at a higher threshold passed the first rule against itself."""
    lab = _lab()
    v1 = _v1(lab)
    for op in (5.0, 5.8, 6.5):
        assert not gate.decide(lab, v1, v1, op, nboot=200)["passed"], op


def test_a_better_model_passes_and_k_below_31_fails():
    lab = _lab()
    v1 = _v1(lab)
    good = _scores(lab, lambda i: 4.1 + 0.1 * int(i[1:]), lambda i: 1.0)
    assert gate.decide(lab, good, v1, 4.0, nboot=200)["passed"]
    picky = _scores(lab, lambda i: 4.1 + 0.1 * int(i[1:]), lambda i: 1.0)
    r = gate.decide(lab, picky, v1, 4.1 + 0.1 * 14 - 1e-9, nboot=200)  # finds 30 of 44
    assert r["k"] == 30 and not r["passed"] and any("k = 30" in x for x in r["reasons"])


def test_an_exact_tie_fails():
    """Δspec = 0 on every resample gives a lower bound of exactly 0, which is not > 0."""
    lab = _lab()
    v1 = _v1(lab)
    pos = [i for i in lab if lab[i]["label"] == "pos"]
    op = gate.t_star(v1, pos, 35)
    r = gate.decide(lab, v1, v1, op, nboot=200)
    assert r["k"] == 35 and r["t_star"] == op and r["lo"] == 0 and not r["passed"]


def test_disputed_rows_never_decide():
    lab = _lab()
    v1 = _v1(lab)
    good = _scores(lab, lambda i: 4.1 + 0.1 * int(i[1:]), lambda i: 1.0)
    base = gate.decide(lab, good, v1, 4.0, nboot=200)
    good["d0"]["weighted_average"] = 9.9  # the candidate now wrongly surfaces the disputed row
    again = gate.decide(lab, good, v1, 4.0, nboot=200)
    assert (base["delta"], base["lo"], base["n_neg"]) == (again["delta"], again["lo"], again["n_neg"])


def test_bootstrap_is_seeded_and_stratified():
    lab = _lab()
    v1 = _v1(lab)
    good = _scores(lab, lambda i: 4.1 + 0.1 * int(i[1:]), lambda i: 1.0)
    a, b = gate.decide(lab, good, v1, 4.0, nboot=300), gate.decide(lab, good, v1, 4.0, nboot=300)
    assert (a["lo"], a["hi"]) == (b["lo"], b["hi"])
    assert a["strata"] == {"hi/gemini_in": 10, "hi/gemini_out_sample": 30, "near/gemini_out_sample": 40}


def test_unscored_labelled_row_raises():
    lab = _lab()
    v1 = _v1(lab)
    cand = dict(v1)
    cand.pop("p0")
    with pytest.raises(SystemExit):
        gate.decide(lab, cand, v1, 4.0, nboot=10)


def test_v1_op_point_is_read_from_its_package():
    assert gate.op_point(gate.V1) == 4.0


def test_candidate_without_training_ids_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="REFUSED"):
        gate.refuse_overlap(tmp_path)


def test_classify_follows_pass_rule_v2():
    c = gate.classify
    assert c("in_scope", "in_scope", "gemini_in") == "pos"
    assert c("in_scope", "out_other", "gemini_in") == "excluded"            # a split
    assert c("cannot_judge", "out_other", "gemini_out_sample") == "excluded"
    assert c("out_one_moment", "out_one_moment", "gemini_in") == "neg"       # the one undisputed class
    assert c("out_one_moment", "out_other", "gemini_in") == "disputed"      # disputed on EITHER pass
    assert c("out_other", "out_other", "gemini_in") == "disputed"
    assert c("out_other", "out_harm_is_story", "gemini_out_sample") == "neg"  # sampled outs always decide


def test_bootstrap_interval_has_width():
    lab = _lab()
    v1 = _v1(lab)
    mixed = _scores(lab, lambda i: 4.1 + 0.1 * int(i[1:]), lambda i: 5.0 if i[-1] in "0" else 1.0)
    r = gate.decide(lab, mixed, v1, 4.0, nboot=300)
    assert r["lo"] < r["delta"] < r["hi"]


def test_ci95_is_the_percentile_interval():
    assert gate.ci95(list(range(2000))[::-1]) == (50, 1949)
    assert gate.NBOOT == 2000 and gate.SEED == 20261009 and gate.K_MIN == 31
