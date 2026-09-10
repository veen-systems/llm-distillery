"""Harm detector v1 — is the article's dominant subject a HARM? (llm-distillery#156)

⛔ **STAMP ONLY. THIS CLASS HAS NO THRESHOLD AND MUST NOT GROW ONE.** It returns a score in
[0,1] and nothing else. ADR-022: *stamp always, decide once — exactly one config-gated drop
point per concern, and every enforcement decision is a config flip.* Whether a lens acts on
the stamp is that lens's config, read where the lens decides, never here.

⛔ **A cross-lens BLOCKER would be wrong, not merely premature.** The same article is harmful
under one lens's promise and constitutive of another's: *"Community kitchens, boat ambulances:
Bihar copes with floods"* betrays Thriving's *"lives getting better"* and is arguably exactly
right under Solutions; Nature Recovery is **about** recovering from damage. Measured: of the 9
articles both judges called harmful, **6 were already surfaced by another lens**.

Architecture (matching `obituary v5`, `violence_promotion v1`, `commerce v2`):

    text -> [frozen paraphrase-multilingual-mpnet-base-v2] -> 768-d -> [scaler] -> 5x MLP -> mean

⭐ **The five heads are not an accuracy trick — they are the fix for `H-DET2`.** With everything
else held fixed, `early_stopping=True` lets `random_state` choose the internal validation split,
and this detector's catch count on the held-out panel spanned **0-3 at the val-picked operating
point**. ⚠️ **Over the 0.30-0.70 plateau single seeds span 2-4, not 0-3, and at 0.30 three of them
catch 4 — beating the ensemble's 3.**

So the ensemble's value is that it removes the CHOICE of seed and is flat across a wide band —
**not that it beats every seed**. Shipping one seed ships a lottery ticket; averaging five removes
the lottery. Cost is negligible: the embedding pass, which dominates, is shared across the heads.

⚠️ **Scores are NOT comparable across library stacks.** The measured **stack** noise floor of
**0.2008** was taken on exactly this architecture (mpnet + sklearn MLP, differing
sentence-transformers versions). Compare scores only within one environment.

Numbers, the shuffled-label null arm, and two refuted predictions: `EXP-037`,
`docs/evidence/2026-09-10-harm-detector/`. ⚠️ Its panel is `uplifting v7` / `human_thriving v8`
display-eligible rows only — it says **nothing** about solutions, belonging, nature_recovery or
cultural_discovery.

Usage:
    from filters.common.harm_detector.v1.inference import HarmDetectorV1

    detector = HarmDetectorV1()
    detector.score(article)              # -> 0.0-1.0
    detector.batch_score(articles)       # -> [float, ...]
"""

import hashlib
import json
import pickle
import re
import warnings
from pathlib import Path
from typing import Optional, Union

MODEL_VERSION = "v1"
EMBEDDER = "paraphrase-multilingual-mpnet-base-v2"


class HarmDetectorV1:
    """Frozen-embedding + 5-head MLP ensemble. Returns a score; decides nothing."""

    def __init__(self, model_dir: Optional[Path] = None, device: str = "cpu"):
        self.device = device
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent / "models"
        self.version = MODEL_VERSION
        self._embedder = None
        self._scaler = None
        self._classifiers = None
        self._config = None

    # ---- lazy loading -----------------------------------------------------
    def _load(self):
        if self._classifiers is not None:
            return
        # ⛔ The import of SentenceTransformer lives BELOW the integrity checks, deliberately.
        # It sat above them until 2026-09-10, which made every cheap refusal here — a
        # mismatched ensemble, a bad hash, a missing manifest — unreachable until a ~7-second
        # ML library had loaded, and unreachable ENTIRELY in a checkout without it, which is
        # where CI runs. Check first, then pay for the model.
        cfg_path = self.model_dir / "training_config.json"
        if not cfg_path.exists():
            raise FileNotFoundError(
                f"{cfg_path} missing — the ensemble's seed list lives there and guessing it "
                f"would silently ship a different model than the one that was measured"
            )
        self._config = json.loads(cfg_path.read_text(encoding="utf-8"))

        declared = list(self._config["ensemble_seeds"])
        on_disk = sorted(int(m.group(1)) for m in (
            re.fullmatch(r"mlp_classifier_seed(\d+)\.pkl", f.name)
            for f in self.model_dir.glob("mlp_classifier_seed*.pkl")) if m)
        # ⛔ BOTH DIRECTIONS. The first version checked only that every DECLARED seed was on
        # disk, so editing `ensemble_seeds` to [0,1] loaded two heads out of five with no
        # error — measured: a 0.083 score shift on identical input, under an IDENTICAL version
        # stamp. "A partial ensemble is a DIFFERENT model" was the stated principle; the code
        # enforced half of it.
        if sorted(declared) != on_disk:
            raise ValueError(
                f"ensemble mismatch: training_config.json declares seeds {sorted(declared)} "
                f"but {self.model_dir} holds {on_disk}. A partial or padded ensemble is a "
                f"DIFFERENT model, not a degraded one — refusing to average whatever is here."
            )
        # ⛔ Verify what we are about to unpickle. SHA256SUMS.txt existed and NOTHING read it,
        # so swapping any pickle for a different model passed every automated check here.
        self._verify_hashes(["scaler.pkl"] + [f"mlp_classifier_seed{s}.pkl" for s in declared])

        with (self.model_dir / "scaler.pkl").open("rb") as f:   # AFTER the hash check, not
            self._scaler = pickle.load(f)                       # before it — see above

        clfs = []
        for seed in declared:
            with (self.model_dir / f"mlp_classifier_seed{seed}.pkl").open("rb") as f:
                clfs.append(pickle.load(f))
        self._classifiers = clfs
        # The version is a property of the ARTIFACT, not of this file. Reading a module
        # constant is how a 2-head load stamped the same string as the measured 5-head one.
        self.version = self._config.get("version", MODEL_VERSION)
        self._warn_on_stack_drift()

        from sentence_transformers import SentenceTransformer
        self._embedder = SentenceTransformer(EMBEDDER, device=self.device)

    def _verify_hashes(self, filenames):
        """Refuse to unpickle a file whose digest matches no recorded one.

        A pickle is arbitrary code; a manifest nothing reads is a comment. Accepts
        `SHA256SUMS.txt` (this repo) or per-file `.sha256` sidecars (the vendored copy).
        """
        expected = {}
        manifest = self.model_dir / "SHA256SUMS.txt"
        if manifest.exists():
            for line in manifest.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if len(parts) == 2:
                    expected[parts[1].lstrip("*")] = parts[0]
        for name in filenames:
            sidecar = self.model_dir / f"{name}.sha256"
            if sidecar.exists():
                expected[name] = sidecar.read_text(encoding="utf-8").strip().split()[0]
        missing = [n for n in filenames if n not in expected]
        if missing:
            raise ValueError(
                f"no recorded hash for {missing} — expected SHA256SUMS.txt or per-file "
                f".sha256 sidecars in {self.model_dir}. Refusing to unpickle unverified code."
            )
        for name in filenames:
            digest = hashlib.sha256((self.model_dir / name).read_bytes()).hexdigest()
            if digest != expected[name]:
                raise ValueError(f"integrity check FAILED for {name}: got {digest[:12]}, "
                                 f"expected {expected[name][:12]}")

    def _warn_on_stack_drift(self):
        """`sklearn_version` was recorded by the builder and read by nothing.

        The measured STACK floor for this architecture is **0.2008** — larger than the batch
        floor — so a version difference is not cosmetic. Warns rather than raises: refusing to
        load would take a lens down over a number that is usually fine.
        """
        built = self._config.get("sklearn_version")
        if not built:
            return
        try:
            import sklearn
        except ImportError:
            return
        if sklearn.__version__ != built:
            warnings.warn(
                f"harm detector was built on scikit-learn {built}, loading under "
                f"{sklearn.__version__}. Scores are NOT comparable across library stacks "
                f"(measured stack floor 0.2008 on this architecture).",
                RuntimeWarning, stacklevel=2)

    # ---- text -------------------------------------------------------------
    @staticmethod
    def _text(article: Union[dict, str]) -> str:
        """Title + content, exactly as the trainer built it. Any drift here is a silent
        distribution shift — the model never sees the field names, only this string."""
        if isinstance(article, str):
            return article.strip()
        return f"{article.get('title') or ''} {article.get('content') or ''}".strip()

    # ---- scoring ----------------------------------------------------------
    def batch_score(self, articles: list, batch_size: int = 32) -> list:
        if not articles:
            return []
        self._load()
        # Cheap refusal BEFORE the expensive embedding — the same ordering mistake as the
        # import above, and it cost an embedding pass to discover there was nothing to score.
        if not self._classifiers:            # zip(*[]) is empty for ANY input, so without
            raise RuntimeError(              # this a caller gets [] for 100 articles, stamps
                "harm detector has no classifier heads loaded"   # nothing, and reports success
            )
        texts = [self._text(a) for a in articles]
        emb = self._embedder.encode(texts, batch_size=batch_size, show_progress_bar=False)
        z = self._scaler.transform(emb)
        stacked = [c.predict_proba(z)[:, 1] for c in self._classifiers]
        scores = [float(sum(col) / len(col)) for col in zip(*stacked)]
        if len(scores) != len(articles):
            raise RuntimeError(
                f"scored {len(scores)} of {len(articles)} articles — refusing to return a "
                f"list the caller would zip against its input"
            )
        return scores

    def score(self, article: Union[dict, str]) -> float:
        return self.batch_score([article])[0]

    def stamp(self, article: Union[dict, str]) -> dict:
        """The row-shaped stamp. No verdict key, deliberately — see the module docstring.

        ⚠️ Keys carry the leading underscore the pipeline writes and both contract strip-lists
        match on (`_harm_`). The first version returned un-prefixed names — dead code nothing
        called, and a name trap for whoever wired it in.
        """
        return {
            "_harm_is_subject_score": round(self.score(article), 6),
            "_harm_detector_model": self.version,
        }
