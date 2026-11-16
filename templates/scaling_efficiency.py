"""Synthetic scaling/efficiency trade-off figure with explicit axis semantics."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figures4papers import FigureContract, finalize_figure
from figures4papers.design_tokens import DOUBLE_COLUMN, DEFAULT_TOKENS, publication_context


def build(output_dir: str | Path):
    params = np.array([12, 28, 62, 125, 250], dtype=float)
    quality = np.array([0.61, 0.68, 0.73, 0.765, 0.781])
    latency = np.array([2.1, 3.0, 4.8, 8.9, 17.2])
    with publication_context():
        fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COLUMN.width_mm / 25.4, 72 / 25.4))
        axes[0].plot(params, quality, marker="o", color=DEFAULT_TOKENS.proposed)
        axes[0].set_xscale("log", base=2)
        axes[0].set_xlabel("Parameters (millions; synthetic)")
        axes[0].set_ylabel("Synthetic task score")
        axes[0].set_title("Quality vs. model size", loc="left", pad=7)
        axes[0].grid(color=DEFAULT_TOKENS.grid, linewidth=0.45)
        axes[0].set_axisbelow(True)

        axes[1].plot(params, latency, marker="s", color=DEFAULT_TOKENS.baseline)
        axes[1].set_xscale("log", base=2)
        axes[1].set_yscale("log")
        axes[1].set_xlabel("Parameters (millions; synthetic)")
        axes[1].set_ylabel("Latency (ms; synthetic)")
        axes[1].set_title("Latency cost vs. model size", loc="left", pad=7)
        axes[1].grid(color=DEFAULT_TOKENS.grid, linewidth=0.45)
        axes[1].set_axisbelow(True)
        fig.tight_layout(w_pad=2)
        contract = FigureContract(
            "v02-scaling-efficiency", "other", "Make the quality and latency costs of scaling visible",
            "Hard-coded synthetic teaching values", "parameters (millions)", "score / latency",
            provenance_note="Two panels use different y-axis units and scales; they must not be compared numerically.",
        )
        paths = finalize_figure(fig, Path(output_dir) / "scaling_efficiency",
                                formats=("png", "pdf", "svg"), contract=contract, crop=False,
                                transformations=["plot synthetic model-size sweep; log2 parameter axis; log latency axis"])
    return paths, []


if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "generated")
