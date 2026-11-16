"""Reproducible synthetic example: grouped model comparison."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figures4papers import (
    FigureContract, apply_publication_style, make_grouped_bar,
    finalize_figure, validate_figure,
)

def build(output_dir: str | Path):
    apply_publication_style()
    fig, ax = plt.subplots(figsize=(7,4))
    make_grouped_bar(ax,
        categories=["Task A", "Task B", "Task C"],
        series=[[0.86,0.84,0.90], [0.78,0.79,0.81]],
        labels=["Proposed (synthetic)", "Baseline (synthetic)"],
        ylabel="Accuracy (fraction)", annotate=True)
    ax.set_xlabel("Evaluation task")
    ax.set_ylim(0,1)
    issues=validate_figure(fig)
    contract=FigureContract("demo-grouped", "grouped_bar", "Synthetic comparison only",
                            "Hard-coded synthetic teaching values", "task", "fraction")
    paths=finalize_figure(fig,Path(output_dir)/"grouped_bar",
                         formats=("png","pdf","svg"), contract=contract,
                         transformations=["No transformation; synthetic example"])
    return paths, issues

if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "figures")
