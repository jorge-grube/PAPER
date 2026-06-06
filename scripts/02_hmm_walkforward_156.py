"""
hmm_walkforward_156.py
----------------------
Walk-forward HMM with MIN_TRAIN_OBS = 156 (3 years).
Canonical state ordering by ascending mean z52_VIX.
Writes to SEPARATE checkpoint + parquets — canonical 260-week results untouched.

Outputs (safe, never overwrites canonical results):
  data/processed/hmm_wf_checkpoint_156.pkl
  data/processed/regime_labels_wf_156.parquet
  data/processed/regime_probs_wf_156.parquet
"""
from __future__ import annotations
import argparse, logging, pickle, sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from models.hmm import (
    WALK_FORWARD_STEP, HMMFitResult,
    fit_hmm, decode_regimes, select_and_impute, REGIME_FEATURES,
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)-7s | %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

PROCESSED     = ROOT / "data" / "processed"
CKPT_PATH     = PROCESSED / "hmm_wf_checkpoint_156.pkl"
MIN_TRAIN_OBS = 156
N_STATES      = 4
VIX_IDX       = 0   # z52_VIX is first in REGIME_FEATURES

def canonical_permutation(result: HMMFitResult) -> np.ndarray:
    vix_means = result.model.means_[:, VIX_IDX]
    return np.argsort(np.argsort(vix_means))   # inv_perm: old→new label

def main(batch_size: int = 20):
    feats_raw = pd.read_parquet(PROCESSED / "regime_features_weekly.parquet")
    X = select_and_impute(feats_raw, REGIME_FEATURES, logger=log)
    n = len(X)
    log.info("Feature matrix: %d×%d  %s..%s",
             n, X.shape[1], X.index[0].date(), X.index[-1].date())

    checkpoints = list(range(MIN_TRAIN_OBS, n + 1, WALK_FORWARD_STEP))
    log.info("MIN_TRAIN=%d  STEP=%d  N_STATES=%d  total_ckpts=%d",
             MIN_TRAIN_OBS, WALK_FORWARD_STEP, N_STATES, len(checkpoints))

    # ── load or init checkpoint ───────────────────────────────────────────────
    if CKPT_PATH.exists():
        with open(CKPT_PATH, "rb") as f:
            ckpt = pickle.load(f)
        valid = (ckpt.get("n") == n and
                 ckpt.get("n_states") == N_STATES and
                 ckpt.get("min_train") == MIN_TRAIN_OBS and
                 ckpt.get("label_switched") is True)
        if not valid:
            log.warning("Checkpoint invalid — starting fresh.")
            ckpt = None
        else:
            done = len(ckpt["completed_ends"])
            log.info("Resuming: %d/%d done (%.1f%%)",
                     done, len(checkpoints), 100*done/len(checkpoints))
    else:
        ckpt = None

    if ckpt is None:
        ckpt = {
            "n": n, "n_states": N_STATES, "min_train": MIN_TRAIN_OBS,
            "label_switched": True,
            "labels":     np.full(n, np.nan),
            "posteriors": np.full((n, N_STATES), np.nan),
            "completed_ends": set(),
            "done": False,
        }

    if ckpt["done"]:
        log.info("Already complete — writing parquets.")
        _write_parquets(ckpt, X)
        return

    todo = [e for e in checkpoints if e not in ckpt["completed_ends"]]
    log.info("%d checkpoints remaining", len(todo))

    for i, end in enumerate(todo[:batch_size]):
        X_train = X.iloc[:end]   # DataFrame — what fit_hmm expects
        result  = fit_hmm(X_train, n_states=N_STATES, logger=log)

        raw_labels     = decode_regimes(result, X_train)
        X_scaled       = result.scaler.transform(X_train.values)
        raw_posteriors = result.model.predict_proba(X_scaled)

        inv_perm  = canonical_permutation(result)
        perm      = np.argsort(inv_perm)   # new→old (for reordering posterior cols)
        can_label = int(inv_perm[int(raw_labels.iloc[-1])])
        can_post  = raw_posteriors[-1][perm]

        ckpt["labels"][end - 1]     = can_label
        ckpt["posteriors"][end - 1] = can_post
        ckpt["completed_ends"].add(end)

    with open(CKPT_PATH, "wb") as f:
        pickle.dump(ckpt, f)

    done  = len(ckpt["completed_ends"])
    total = len(checkpoints)
    log.info("Saved: %d/%d (%.1f%%) — %d remaining",
             done, total, 100*done/total, total - done)

    if done >= total:
        ckpt["done"] = True
        with open(CKPT_PATH, "wb") as f:
            pickle.dump(ckpt, f)
        log.info("All checkpoints complete.")

    _write_parquets(ckpt, X)


def _write_parquets(ckpt, X):
    lab = pd.Series(ckpt["labels"], index=X.index, name="regime_wf")
    prb = pd.DataFrame(ckpt["posteriors"], index=X.index,
                       columns=[f"prob_state_{k}" for k in range(N_STATES)])
    n_valid = lab.notna().sum()
    if n_valid > 0:
        log.info("Valid labels: %d  first=%s  last=%s",
                 n_valid, lab.dropna().index.min().date(), lab.dropna().index.max().date())
    lab.to_frame().to_parquet(PROCESSED / "regime_labels_wf_156.parquet")
    prb.to_parquet(PROCESSED / "regime_probs_wf_156.parquet")
    log.info("Parquets written.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=20)
    args = ap.parse_args()
    main(batch_size=args.batch_size)
