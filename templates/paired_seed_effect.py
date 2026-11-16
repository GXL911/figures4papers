"""Synthetic paired-seed effect plot designed for a single-column (89 mm) figure."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import t

from figures4papers import FigureContract, finalize_figure
from figures4papers.design_tokens import SINGLE_COLUMN, DEFAULT_TOKENS, publication_context


def build(output_dir: str | Path):
    rng = np.random.default_rng(2026)
    baseline = rng.normal(0.742, 0.018, size=12)
    paired_gain = rng.normal(0.031, 0.012, size=12)
    proposed = baseline + paired_gain
    delta = proposed - baseline
    mean = float(delta.mean())
    sem = float(delta.std(ddof=1) / np.sqrt(delta.size))
    half = float(t.ppf(0.975, delta.size - 1) * sem)

    with publication_context():
        fig, axes = plt.subplots(2, 1, figsize=(SINGLE_COLUMN.width_mm / 25.4, 108 / 25.4),
                                 gridspec_kw={"height_ratios": [1.2, 1]})
        ax = axes[0]
        x = np.array([0, 1])
        for b, p in zip(baseline, proposed):
            ax.plot(x, [b, p], color=DEFAULT_TOKENS.neutral, linewidth=0.8, alpha=0.85, zorder=1)
        ax.scatter(np.zeros_like(baseline), baseline, s=17, color=DEFAULT_TOKENS.baseline,
                   edgecolor="white", linewidth=0.35, zorder=2, label="Baseline")
        ax.scatter(np.ones_like(proposed), proposed, s=17, color=DEFAULT_TOKENS.proposed,
                   edgecolor="white", linewidth=0.35, zorder=2, label="Proposed")
        ax.set_xticks([0, 1], ["Baseline", "Proposed"])
        ax.set_ylabel("Score (fraction)")
        ax.set_title("(a) Paired results by seed", loc="left", pad=5)
        ax.grid(axis="y", color=DEFAULT_TOKENS.grid, linewidth=0.45)
        ax.set_axisbelow(True)
        ax.legend(ncol=2, loc="lower right")

        ax = axes[1]
        jitter = rng.normal(0, 0.035, size=delta.size)
        ax.scatter(delta, jitter, s=22, color=DEFAULT_TOKENS.proposed,
                   edgecolor="white", linewidth=0.4, zorder=3)
        ax.axvline(0, color=DEFAULT_TOKENS.muted, linewidth=0.9, linestyle="--", label="No change")
        ax.axvline(mean, color=DEFAULT_TOKENS.baseline, linewidth=1.4, label="Mean difference")
        ax.axvspan(mean-half, mean+half, color=DEFAULT_TOKENS.baseline, alpha=0.16, linewidth=0)
        ax.set_yticks([])
        ax.set_xlabel("Paired difference (Proposed − Baseline)")
        ax.set_title("(b) Effect across seeds", loc="left", pad=5)
        ax.text(0.03, 0.96, f"Mean = {mean:.3f}\n95% t interval [{mean-half:.3f}, {mean+half:.3f}]",
                transform=ax.transAxes, va="top", ha="left", fontsize=8.0)
        ax.grid(axis="x", color=DEFAULT_TOKENS.grid, linewidth=0.45)
        ax.set_axisbelow(True)
        fig.tight_layout(h_pad=1.2)
        contract = FigureContract(
            "v02-paired-seed-effect", "other", "Show paired seed-level outcomes and their differences",
            "Deterministic synthetic teaching data; 12 paired seeds", "method / paired difference",
            "score fraction", uncertainty_kind="ci",
            provenance_note="95% Student-t interval computed across 12 independent paired seed differences.",
        )
        paths = finalize_figure(fig, Path(output_dir) / "paired_seed_effect",
                                formats=("png", "pdf", "svg"), contract=contract, crop=False,
                                seed=2026, transformations=["paired difference proposed minus baseline",
                                "two-sided 95% Student-t interval across independent seeds"])
    return paths, []


if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "generated")
