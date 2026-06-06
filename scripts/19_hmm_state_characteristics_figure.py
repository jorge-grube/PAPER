"""
19_hmm_state_characteristics_figure.py
---------------------------------------
Figure: HMM State Characteristics — mean z-score by state for key features.
Professional grouped bar chart for MDPI Economies paper.
Values are from the full-sample descriptive HMM (Table 2).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── Data from Table 2 ─────────────────────────────────────────────────────────
STATES = ["State 0\nLow-vol / Subdued", "State 1\nRisk-on / Expansion",
          "State 2\nNeutral / Moderate", "State 3\nElevated-risk / Stress"]

FEATURES = ["z-VIX", "z-ESI", "z-Spread", "z-Slope"]

VALUES = {
    "z-VIX":    [-0.96, -0.59,  0.05,  1.84],
    "z-ESI":    [-0.33,  1.49, -0.73, -0.74],
    "z-Spread": [-0.31, -0.57,  0.15,  0.45],
    "z-Slope":  [-1.31,  0.70, -0.36,  0.10],
}

# ── Palette aligned with regime colours in Figure 1 ───────────────────────────
STATE_COLORS = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]

FEATURE_HATCHES = ["", "///", "...", "xxx"]
FEATURE_ALPHAS  = [0.90, 0.85, 0.80, 0.75]

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5))

n_states   = len(STATES)
n_features = len(FEATURES)
group_w    = 0.65          # total width of a state's bar group
bar_w      = group_w / n_features
x_base     = np.arange(n_states)

for fi, feat in enumerate(FEATURES):
    offsets = (fi - (n_features - 1) / 2) * bar_w
    xpos = x_base + offsets
    vals = VALUES[feat]
    bars = ax.bar(
        xpos, vals, width=bar_w * 0.92,
        color=[STATE_COLORS[si] for si in range(n_states)],
        hatch=FEATURE_HATCHES[fi],
        alpha=FEATURE_ALPHAS[fi],
        edgecolor="white", linewidth=0.4,
        label=feat if fi == 0 else None,   # labels handled via custom legend
    )

# Zero line
ax.axhline(0, color="black", linewidth=0.7, linestyle="-")

# State x-labels
ax.set_xticks(x_base)
ax.set_xticklabels(STATES, fontsize=9, ha="center")
ax.set_ylabel("Mean 52-week z-score", fontsize=10)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle="--", linewidth=0.4, alpha=0.5)

# ── Legend: features ──────────────────────────────────────────────────────────
feature_patches = []
for fi, feat in enumerate(FEATURES):
    patch = mpatches.Patch(
        facecolor="grey", hatch=FEATURE_HATCHES[fi],
        alpha=FEATURE_ALPHAS[fi], edgecolor="white", linewidth=0.4,
        label=feat
    )
    feature_patches.append(patch)

ax.legend(
    handles=feature_patches, title="Feature", title_fontsize=8.5,
    fontsize=8.5, loc="upper left", framealpha=0.9, edgecolor="gray",
    ncol=2,
)

fig.tight_layout()

out_dir = ROOT / "reports" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "figure_2_hmm_state_characteristics.png"
fig.savefig(out_path, dpi=180, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {out_path}")

paper_fig_dir = ROOT / "paper" / "figures"
paper_fig_dir.mkdir(parents=True, exist_ok=True)
import shutil
shutil.copy2(out_path, paper_fig_dir / "figure_2_hmm_state_characteristics.png")
print(f"Copied to paper/figures/")
