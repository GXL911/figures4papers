"""Synthetic factorial ablation matrix; rows/columns are named interventions."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figures4papers import FigureContract, finalize_figure
from figures4papers.design_tokens import SINGLE_COLUMN, DEFAULT_TOKENS, publication_context


def build(output_dir: str | Path):
    # Synthetic scores deliberately include non-additive interactions.
    matrix = np.array([
        [0.701, 0.724, 0.739, 0.746],
        [0.718, 0.751, 0.762, 0.773],
        [0.727, 0.759, 0.781, 0.792],
        [0.733, 0.766, 0.795, 0.814],
    ])
    labels = ["None", "Crop", "Color", "Blur"]
    with publication_context():
        fig, ax = plt.subplots(figsize=(SINGLE_COLUMN.width_mm / 25.4, 89 / 25.4))
        image = ax.imshow(matrix, cmap="cividis", vmin=0.68, vmax=0.83, aspect="equal")
        ax.set_xticks(np.arange(4), labels)
        ax.set_yticks(np.arange(4), labels)
        ax.set_xlabel("Second intervention")
        ax.set_ylabel("First intervention")
        ax.set_title("Ablation matrix", loc="left", pad=8, fontsize=9)
        for row in range(4):
            for col in range(4):
                color = "white" if matrix[row, col] < 0.735 else "#17212B"
                ax.text(col, row, f"{matrix[row, col]:.3f}", ha="center", va="center",
                        color=color, fontsize=8, fontweight="bold")
        cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
        cbar.set_label("Synthetic top-1 accuracy (fraction)")
        ax.set_xticks(np.arange(-0.5, 4, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, 4, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.2)
        ax.tick_params(which="minor", bottom=False, left=False)
        fig.tight_layout()
        contract = FigureContract(
            "v02-ablation-matrix", "heatmap", "Show main effects and pairwise intervention interactions",
            "Hard-coded synthetic teaching values; not reproduced SimCLR measurements",
            "second intervention", "first intervention / synthetic accuracy",
            provenance_note="Rows and columns are design factors; diagonal entries are single-factor conditions.",
        )
        paths = finalize_figure(fig, Path(output_dir) / "ablation_matrix",
                                formats=("png", "pdf", "svg"), contract=contract, crop=False,
                                transformations=["plot synthetic 4x4 intervention matrix with fixed color limits 0.68 to 0.83"])
    return paths, []


if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "generated")
