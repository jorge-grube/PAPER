"""
09_regime_timeline_figure.py
-----------------------------
Descriptive figure: full-sample HMM regime timeline (2004–2026).
Uses regime_labels_full.parquet (in-sample labels, all data used for fitting).

IMPORTANT: These are in-sample labels — the HMM was fit to the full dataset.
They are used here for descriptive illustration only and are NOT used in any
OOS trading simulation.

Outputs:
  reports/figures/full_sample_regime_timeline.png
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# ── palette ───────────────────────────────────────────────────────────────────
# 4 states ordered by ascending VIX (0 = lowest VIX / most subdued, 3 = highest VIX / stress)
# Labels aligned with paper text (Section 3.1) and build_paper_ECONOMIES.js:
#   0 → Low-vol / Subdued       (VIX z-score ≈ −0.96)
#   1 → Risk-on / Expansion     (VIX z-score ≈ −0.59)
#   2 → Neutral / Moderate      (VIX z-score ≈ +0.05)
#   3 → Elevated-risk / Stress  (VIX z-score ≈ +1.85)

REGIME_LABELS = {
    0: "Low-vol/Subdued",
    1: "Risk-on/Expansion",
    2: "Neutral/Moderate",
    3: "Elevated-risk/Stress",
}

REGIME_COLORS = {
    0: "#1f77b4",   # blue    — low-vol/subdued
    1: "#2ca02c",   # green   — risk-on/expansion
    2: "#ff7f0e",   # orange  — neutral/moderate
    3: "#d62728",   # red     — elevated-risk/stress
}

# ── crisis annotations ────────────────────────────────────────────────────────
EVENTS = [
    ("GFC",             "2008-09-15", "2009-06-30"),   # Lehman to trough
    ("EZ Debt Crisis",  "2010-04-23", "2012-09-06"),   # Greece bail-out to Draghi's "whatever it takes"
    ("COVID Crash",     "2020-02-24", "2020-05-18"),   # Peak → recovery
    ("Inflation Shock", "2022-01-01", "2023-01-01"),   # Rate-hike cycle
]


def _make_spans(labels: pd.Series, state: int):
    """Return list of (start, end) date pairs for contiguous blocks of `state`."""
    mask = (labels == state)
    spans = []
    in_span = False
    s_start = None
    idx = labels.index
    for i, (dt, val) in enumerate(mask.items()):
        if val and not in_span:
            s_start = dt
            in_span = True
        elif not val and in_span:
            # span ended at previous date; extend half-week forward for display
            spans.append((s_start, idx[i - 1] + pd.Timedelta(days=3)))
            in_span = False
    if in_span:
        spans.append((s_start, idx[-1] + pd.Timedelta(days=3)))
    return spans


def main():
    processed = ROOT / "data" / "processed"
    fig_dir   = ROOT / "reports" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # ── load labels & STOXX return for context ────────────────────────────────
    lab = pd.read_parquet(processed / "regime_labels_full.parquet")
    lab.index = pd.to_datetime(lab.index)
    lab_s = lab["regime_full"]

    ret = pd.read_parquet(processed / "investable_returns_weekly.parquet")
    ret.index = pd.to_datetime(ret.index)
    stoxx_r = ret["StoxxEurope600"].reindex(lab_s.index).fillna(0.0)
    stoxx_cum = (1 + stoxx_r).cumprod()

    # ── figure layout ─────────────────────────────────────────────────────────
    fig, (ax_top, ax_bot) = plt.subplots(
        2, 1, figsize=(14, 7),
        gridspec_kw={"height_ratios": [1, 2]},
        sharex=True,
    )
    fig.subplots_adjust(hspace=0.08)

    # ── top panel: regime bars ─────────────────────────────────────────────────
    for state, color in REGIME_COLORS.items():
        spans = _make_spans(lab_s, state)
        for (s, e) in spans:
            ax_top.axvspan(s, e, color=color, alpha=0.85, linewidth=0)

    ax_top.set_ylim(0, 1)
    ax_top.set_yticks([])
    ax_top.set_ylabel("Regime", fontsize=10, labelpad=6)
    ax_top.tick_params(bottom=False)
    ax_top.spines["top"].set_visible(False)
    ax_top.spines["right"].set_visible(False)
    ax_top.spines["left"].set_visible(False)
    ax_top.spines["bottom"].set_visible(False)

    # legend
    patches = [
        mpatches.Patch(color=REGIME_COLORS[s], label=REGIME_LABELS[s])
        for s in [0, 1, 2, 3]   # ordered: low-vol → risk-on → neutral → elevated-risk
    ]
    ax_top.legend(
        handles=patches, ncol=4, loc="upper left",
        fontsize=8.5, framealpha=0.9, edgecolor="gray",
    )

    # in-sample notice
    ax_top.text(
        0.99, 0.5,
        "IN-SAMPLE labels only - NOT used for OOS trading",
        transform=ax_top.transAxes,
        ha="right", va="center",
        fontsize=8, color="#555555",
        style="italic",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow",
                  edgecolor="#aaaaaa", alpha=0.9),
    )

    # ── bottom panel: STOXX 600 cumulative return ─────────────────────────────
    ax_bot.plot(stoxx_cum.index, stoxx_cum.values, color="#222222",
                linewidth=1.1, label="STOXX Europe 600 (cum. return)")

    # shade same regime colours in bottom panel (lighter)
    for state, color in REGIME_COLORS.items():
        spans = _make_spans(lab_s, state)
        for (s, e) in spans:
            ax_bot.axvspan(s, e, color=color, alpha=0.12, linewidth=0)

    # annotate crisis events
    y_min = stoxx_cum.min()
    y_max = stoxx_cum.max()
    y_range = y_max - y_min
    for label, start, end in EVENTS:
        s_dt = pd.Timestamp(start)
        e_dt = pd.Timestamp(end)
        ax_bot.axvspan(s_dt, e_dt, color="gray", alpha=0.18, linewidth=0)
        mid = s_dt + (e_dt - s_dt) / 2
        ax_bot.annotate(
            label,
            xy=(mid, y_min + 0.03 * y_range),
            ha="center", va="bottom",
            fontsize=7.5, color="#333333",
            rotation=0,
        )

    ax_bot.set_ylabel("Cumulative Return (1 = start)", fontsize=10)
    ax_bot.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))
    ax_bot.spines["top"].set_visible(False)
    ax_bot.spines["right"].set_visible(False)
    ax_bot.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.5)

    # x-axis formatting
    import matplotlib.dates as mdates
    ax_bot.xaxis.set_major_locator(mdates.YearLocator(2))
    ax_bot.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.setp(ax_bot.xaxis.get_majorticklabels(), rotation=0, ha="center", fontsize=9)

    # ── no embedded caption text — figure title and caption are provided by DOCX ─
    # (Removed fig.text() call: descriptive caption belongs in the DOCX figure caption,
    #  not embedded in the image itself.)

    out_path = fig_dir / "full_sample_regime_timeline.png"
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")

    # Also save to paper/figures/ for build_paper_ECONOMIES.js
    paper_fig_dir = ROOT / "paper" / "figures"
    paper_fig_dir.mkdir(parents=True, exist_ok=True)
    paper_out = paper_fig_dir / "figure_1_regime_timeline.png"
    import shutil
    shutil.copy2(out_path, paper_out)
    print(f"Copied to: {paper_out}")


if __name__ == "__main__":
    main()
