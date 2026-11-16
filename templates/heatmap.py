"""Small synthetic benchmark performance matrix."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figures4papers import (
    FigureContract, apply_publication_style, make_heatmap,
    validate_figure, finalize_figure,
)

def build(output_dir: str | Path):
    apply_publication_style()
    fig,ax=plt.subplots(figsize=(6,4))
    make_heatmap(ax,[[0.80,0.70,0.65],[0.90,0.82,0.77]],
                 x_labels=["Task A","Task B","Task C"],
                 y_labels=["Proposed","Baseline"],
                 cbar_label="Accuracy (fraction)",annotate=True,vmin=0,vmax=1)
    ax.set(xlabel="Evaluation task",ylabel="Method")
    issues=validate_figure(fig)
    contract=FigureContract("demo-heatmap","heatmap","Synthetic benchmark scores",
                            "Hard-coded synthetic teaching values","task","fraction")
    paths=finalize_figure(fig,Path(output_dir)/"heatmap",
                          formats=("png","pdf","svg"),contract=contract)
    return paths,issues

if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "figures")
