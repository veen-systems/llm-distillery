"""#179: the agreement statistics against published values, and the prevalence paradox they exist for."""
import pytest

from ground_truth import agreement as ag

# Krippendorff (2011), "Computing Krippendorff's Alpha-Reliability", the 4-coder x 12-unit example with
# missing values. Published: nominal 0.743, ordinal 0.815, interval 0.849.
_ = None
CODERS = [
    [1, 2, 3, 3, 2, 1, 4, 1, 2, _, _, _],
    [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, _, 3],
    [_, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, _],
    [1, 2, 3, 3, 2, 4, 4, 1, 2, 5, 1, _],
]
UNITS = list(zip(*CODERS))


@pytest.mark.parametrize("level,published", [("nominal", 0.743), ("ordinal", 0.815), ("interval", 0.849)])
def test_alpha_reproduces_krippendorffs_worked_example(level, published):
    assert ag.krippendorff_alpha(UNITS, level) == pytest.approx(published, abs=5e-4)


def test_kappa_matches_sklearn():
    sk = pytest.importorskip("sklearn.metrics")
    a = ["in", "out", "out", "in", "out", "out", "in", "out"]
    b = ["in", "out", "in", "in", "out", "out", "out", "out"]
    assert ag.cohen_kappa(a, b) == pytest.approx(sk.cohen_kappa_score(a, b))


def test_ac1_by_hand():
    # n=10, agree 8. pi(in) = (3+3)/20 = 0.3; pe = 2*0.3*0.7/(2-1) = 0.42; AC1 = (0.8-0.42)/0.58
    a = ["in"] * 3 + ["out"] * 7
    b = ["in"] * 2 + ["out"] + ["in"] + ["out"] * 6
    assert ag.gwet_ac1(a, b) == pytest.approx((0.8 - 0.42) / 0.58)


def test_the_PREVALENCE_PARADOX_raw_is_high_and_kappa_is_not():
    """The #179 case: a rare positive class. 96% raw agreement, kappa/alpha near zero, AC1 stays high."""
    a = ["out"] * 96 + ["in", "in", "out", "out"]
    b = ["out"] * 96 + ["out", "out", "in", "in"]
    r = ag.agreement_report(a, b, positive="in")
    assert r["raw"] == pytest.approx(0.96)
    assert r["kappa"] < 0.0 and r["alpha_nominal"] < 0.0
    assert r["ac1"] > 0.9
    assert r["positive_rate"] == (0.02, 0.02)


def test_undefined_statistics_RAISE_never_read_as_perfect():
    with pytest.raises(ValueError):
        ag.cohen_kappa(["out"] * 5, ["out"] * 5)
    with pytest.raises(ValueError):
        ag.krippendorff_alpha([("out", "out")] * 5)
    with pytest.raises(ValueError):
        ag.krippendorff_alpha([(1, None), (None, 2)])
    with pytest.raises(ValueError):
        ag.gwet_ac1(["in"], ["in"])
    with pytest.raises(ValueError):
        ag.raw_agreement(["in"], ["in", "out"])
    with pytest.raises(ValueError):
        ag.gwet_ac1(["in", "x"], ["in", "out"], categories=["in", "out"])


def test_an_unused_category_enters_ac1s_chance_term():
    a, b = ["in", "out", "out", "out"], ["in", "out", "out", "in"]
    assert ag.gwet_ac1(a, b, categories=["in", "out", "unclear"]) != pytest.approx(ag.gwet_ac1(a, b))
