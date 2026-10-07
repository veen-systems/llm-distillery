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


def test_candidate_without_training_manifest_is_refused(tmp_path):
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


# ---- refusals (review 2026-10-07, guarantees lens: two forged PASSes and four unreachable checks) ----

def test_unscored_rows_raise_instead_of_counting_as_rejections():
    """The blocker: stage_used None (an invalid article) or a NaN score made every negative 'out' -> PASS."""
    for bad in (dict(stage_used=None, weighted_average=0.0), dict(stage_used="stage2", weighted_average=float("nan")),
                dict(stage_used="stage2", weighted_average=None), dict(stage_used="stage2", weighted_average=True)):
        with pytest.raises(SystemExit):
            gate.is_in(bad, 4.0)
    lab = _lab()
    v1 = _v1(lab)
    forged = {i: (dict(stage_used=None, weighted_average=0.0) if x["label"] == "neg" else v1[i]) for i, x in lab.items()}
    with pytest.raises(SystemExit):
        gate.decide(lab, forged, v1, 4.0, nboot=10)


def _write_scores(path, order, ids, rows=None):
    seq = sorted(ids)[::-1] if order == "reversed" else sorted(ids)
    with open(path, "w") as f:
        f.write(gate.json.dumps(dict(meta=dict(order=order, n=len(seq)))) + "\n")
        for i in (rows or seq):
            f.write(gate.json.dumps(dict(id=i, stage_used="stage2", weighted_average=5.0)) + "\n")


def test_load_scores_refuses_a_forward_file_posing_as_reversed(tmp_path):
    ids = ["a", "b", "c"]
    _write_scores(tmp_path / "f.jsonl", "forward", ids)
    gate.load_scores(tmp_path / "f.jsonl", "forward", ids)
    with pytest.raises(SystemExit, match="meta order"):
        gate.load_scores(tmp_path / "f.jsonl", "reversed", ids)
    _write_scores(tmp_path / "r.jsonl", "reversed", ids, rows=sorted(ids))  # meta edited, rows not reordered
    with pytest.raises(SystemExit, match="reversed order"):
        gate.load_scores(tmp_path / "r.jsonl", "reversed", ids)
    _write_scores(tmp_path / "short.jsonl", "forward", ids, rows=["a", "b"])
    with pytest.raises(SystemExit):
        gate.load_scores(tmp_path / "short.jsonl", "forward", ids)


BODY = " ".join(f"word{i}" for i in range(200))  # 200 distinct words: a story body with no repeated runs
HELD = [dict(id="held_1", url="https://www.example.org/story/one?utm_source=x", title="A long held-out story title here",
             content="Rwanda: " + BODY)]


def _row(**kw):
    r = dict(id="other", url="https://other.org/a", title="An unrelated training title here",
             text_head=" ".join(f"other{i}" for i in range(200)))
    r.update(kw)
    return r


def _manifest(tmp_path, rows):
    (tmp_path / gate.TRAINING_MANIFEST).write_text("".join(gate.json.dumps(r) + "\n" for r in rows))


@pytest.mark.parametrize("row,key", [
    (_row(id="held_1"), "id"),
    (_row(url="http://example.org/story/one/"), "url"),
    (_row(title="A LONG held-out story-title here!"), "title"),
    (_row(text_head="KIGALI (newtimes) — " + BODY), "content"),  # a syndicated copy: other id, url, title, prefix
])
def test_overlap_is_refused_by_id_url_title_or_content(tmp_path, row, key):
    _manifest(tmp_path, [row])
    with pytest.raises(SystemExit, match=f"by {key}"):
        gate.refuse_overlap(tmp_path, held=HELD)


def test_clean_manifest_passes_and_short_titles_do_not_collide(tmp_path):
    _manifest(tmp_path, [_row(title="Editorial")])
    held = HELD + [dict(id="h2", url="z", title="Editorial", content="")]
    assert "0 of the 2 held-out" in gate.refuse_overlap(tmp_path, held=held)


def test_an_id_only_manifest_is_refused(tmp_path):
    _manifest(tmp_path, [dict(id="x")])
    with pytest.raises(SystemExit, match="lack id/url/title/text_head"):
        gate.refuse_overlap(tmp_path, held=HELD)


def test_non_latin_titles_stay_matchable():
    assert gate._norm_title("Η κοινότητα επισκευάζει τη στέγη μαζί") is not None
    assert gate._norm_title("Η κοινότητα επισκευάζει τη στέγη μαζί!") == gate._norm_title("η κοινότητα επισκευάζει τη στέγη μαζί")


def test_docs_and_editor_files_do_not_change_the_fingerprint(tmp_path):
    (tmp_path / "adapter.safetensors").write_bytes(b"w")
    before = gate.pkg_fingerprint(tmp_path)
    (tmp_path / "README.md").write_text("gate result: PASS")
    (tmp_path / ".base_scorer.py.swp").write_bytes(b"x")
    assert gate.pkg_fingerprint(tmp_path) == before
    (tmp_path / "config.yaml").write_text("x: 1")
    assert gate.pkg_fingerprint(tmp_path) != before


def test_fingerprint_follows_a_symlinked_model_folder(tmp_path):
    real = tmp_path / "elsewhere"; real.mkdir()
    (real / "adapter.safetensors").write_bytes(b"one")
    pkg = tmp_path / "pkg"; pkg.mkdir()
    (pkg / "model").symlink_to(real, target_is_directory=True)
    before = gate.pkg_fingerprint(pkg)
    (real / "adapter.safetensors").write_bytes(b"two")
    assert before[1] == 1 and gate.pkg_fingerprint(pkg) != before


def _pkg(tmp_path, medium, raw_min=None):
    (tmp_path / "base_scorer.py").write_text(
        f'class S:\n    TIER_THRESHOLDS = [("high", 7.0, "d"), ("medium", {medium}, "d"), ("low", 0.0, "d")]\n')
    if raw_min is not None:
        (tmp_path / "normalization.json").write_text(gate.json.dumps(dict(stats=dict(raw_min=raw_min))))
    return tmp_path


def test_op_point_guards(tmp_path):
    assert gate.op_point(_pkg(tmp_path / "a", 4.25) if (tmp_path / "a").mkdir() is None else None) == 4.25
    (tmp_path / "b").mkdir()
    with pytest.raises(SystemExit, match="falls back"):
        gate.op_point(_pkg(tmp_path / "b", 4.75))
    (tmp_path / "c").mkdir()
    with pytest.raises(SystemExit, match="raw_min"):
        gate.op_point(_pkg(tmp_path / "c", 4.0, raw_min=4.2))


def test_url_normalisation_keeps_article_ids_in_the_query():
    n = gate._norm_url
    assert n("https://www.aib.media/?p=167850") != n("https://www.aib.media/?p=167985")
    assert n("http://example.org/a/?utm_source=x&fbclid=y#top") == n("https://www.example.org/a")


def test_boilerplate_shared_across_rows_is_not_a_twin():
    footer = " ".join(f"cookie{i}" for i in range(60))
    held = [dict(id=f"h{j}", url="", title="", content=f"intro{j} " * 10 + footer) for j in range(3)]
    train = [dict(id="t", text_head="lead " * 10 + footer)]
    assert gate.content_twins(train, held) == []  # the footer's runs occur in 3 held rows: not distinctive
    assert gate.content_twins([dict(id="t", text_head="KIGALI — " + BODY)], HELD)[0][:2] == ("t", "held_1")
