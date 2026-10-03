"""The belonging rubric v2.2 is FROZEN for the held-out measurement and the retrain gate
(docs/evidence/2026-10-03-belonging-heldout/PREREGISTRATION.md, GATE.md). Any edit to the rubric means a NEW
held-out set: the gate's labels were made under exactly this text. Review 2026-10-03 found the freeze enforced only
by scripts that had already run."""
import hashlib
from pathlib import Path

RUBRIC = Path(__file__).resolve().parents[2] / "docs" / "evidence" / "2026-10-02-belonging-adjudication" / "rubric_belonging_v2.md"


def test_belonging_rubric_v2_2_is_frozen():
    assert hashlib.sha256(RUBRIC.read_bytes()).hexdigest()[:16] == "d450b79510418cf7", (
        "rubric_belonging_v2.md changed: the held-out labels and the retrain gate were made under v2.2. "
        "A rubric change needs a new held-out set (PREREGISTRATION.md) before any gate result is read.")
