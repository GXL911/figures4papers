"""Synthetic qualitative/quantitative composite; no paper images are copied."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figures4papers import FigureContract, finalize_figure
from figures4papers.design_tokens import DOUBLE_COLUMN, DEFAULT_TOKENS, publication_context


def _toy_case(seed: int, size: int = 48):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[-1:1:complex(size), -1:1:complex(size)]
    cx, cy = rng.uniform(-0.22, 0.22, size=2)
    rx, ry = rng.uniform(0.28, 0.48, size=2)
    mask = (((xx-cx)/rx)**2 + ((yy-cy)/ry)**2) <= 1
    distractor = np.exp(-((xx+0.58)**2 + (yy-0.48)**2) / 0.045)
    attention = np.exp(-(((xx-cx)*1.12)**2 + ((yy-cy)*1.12)**2) / 0.20) + 0.30*distractor
    attention = (attention - attention.min()) / (attention.max() - attention.min())
    noisy = np.clip(mask.astype(float) + rng.normal(0, 0.12, size=(size, size)), 0, 1)
    return noisy, mask, attention


def build(output_dir: str | Path):
    cases = [_toy_case(seed) for seed in (3, 7, 11)]
    # A thresholded attention map is evaluated against the toy mask only to
    # demonstrate the visual/quantitative pairing, not to imply model results.
    scores = []
    for _, mask, attention in cases:
        pred = attention >= np.quantile(attention, 0.62)
        intersection = np.logical_and(pred, mask).sum()
        union = np.logical_or(pred, mask).sum()
        scores.append(intersection / union if union else 0.0)

    with publication_context():
        fig = plt.figure(figsize=(DOUBLE_COLUMN.width_mm / 25.4, 105 / 25.4))
        grid = fig.add_gridspec(3, 4, width_ratios=[1, 1, 1, 0.9], wspace=0.18, hspace=0.24)
        headers = ["Toy input", "Attention", "Overlay", "Toy IoU"]
        for col, header in enumerate(headers):
            ax = fig.add_subplot(grid[0, col])
            ax.set_title(header, fontsize=8.5, loc="left", pad=5)
            ax.axis("off")
            if col == 3:
                ax.text(0, 0.3, "Synthetic\nexamples", transform=ax.transAxes, fontsize=8)
        for row, (image, mask, attention) in enumerate(cases):
            a0 = fig.add_subplot(grid[row, 0])
            a0.imshow(image, cmap="gray", vmin=0, vmax=1)
            a1 = fig.add_subplot(grid[row, 1])
            a1.imshow(attention, cmap="magma", vmin=0, vmax=1)
            a2 = fig.add_subplot(grid[row, 2])
            a2.imshow(image, cmap="gray", vmin=0, vmax=1)
            a2.imshow(attention, cmap="magma", alpha=0.48, vmin=0, vmax=1)
            for ax in (a0, a1, a2):
                ax.set_xticks([]); ax.set_yticks([])
                for spine in ax.spines.values():
                    spine.set_visible(False)
            a3 = fig.add_subplot(grid[row, 3])
            a3.barh([0], [scores[row]], color=DEFAULT_TOKENS.proposed, height=0.48)
            a3.set_xlim(0, 1)
            a3.set_yticks([])
            a3.set_xlabel("IoU", fontsize=8, labelpad=1)
            a3.text(scores[row] + 0.025, 0, f"{scores[row]:.2f}", va="center", fontsize=8)
            a3.spines[["top", "right", "left"]].set_visible(False)
            a3.tick_params(axis="x", labelsize=8, length=2)
        fig.suptitle("Qualitative evidence paired with a toy quantitative check", x=0.06,
                     y=0.99, ha="left", fontsize=9, fontweight="bold")
        fig.text(0.06, 0.005, "Synthetic geometric masks and attention fields; not DINO outputs or benchmark results.", fontsize=8)
        fig.subplots_adjust(left=0.06, right=0.98, top=0.91, bottom=0.12)
        contract = FigureContract(
            "v02-qualitative-quantitative", "other", "Pair a visual model output with an explicit quantitative check",
            "Deterministic synthetic geometric masks and attention fields", "toy example", "IoU (fraction)",
            provenance_note="Attention threshold is the within-example 62nd percentile; IoU is computed against synthetic masks.",
        )
        paths = finalize_figure(fig, Path(output_dir) / "qualitative_quantitative",
                                formats=("png", "pdf", "svg"), contract=contract, seed=3, crop=False,
                                transformations=["generate three synthetic geometric masks and attention fields",
                                "threshold each attention field at its 62nd percentile",
                                "compute intersection-over-union against synthetic masks"])
    return paths, []


if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "generated")
