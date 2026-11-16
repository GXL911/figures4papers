"""Synthetic independent-seed experiment; never confuse with measured results."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figures4papers import (
    FigureContract, UncertaintySpec, summarize_seeds,
    apply_publication_style, make_learning_curves, validate_figure,
    finalize_figure,
)

def build(output_dir: str | Path):
    rng=np.random.default_rng(17)
    x=np.arange(1,31)
    mean_a=0.4+0.45*(1-np.exp(-x/12))
    mean_b=0.35+0.38*(1-np.exp(-x/15))
    seeds=np.stack([rng.normal(mean_a,0.05,size=(8,len(x))),
                    rng.normal(mean_b,0.05,size=(8,len(x)))], axis=1)
    s=summarize_seeds(seeds, UncertaintySpec("ci", confidence_level=0.95))
    apply_publication_style()
    fig,ax=plt.subplots(figsize=(7,4))
    make_learning_curves(ax,x,s.mean,["Proposed (synthetic)","Baseline (synthetic)"],
                         lower=s.lower,upper=s.upper,
                         uncertainty_kind="ci",ylabel="Accuracy (fraction)")
    ax.set_ylim(0,1)
    issues=validate_figure(fig)
    contract=FigureContract("demo-learning","learning_curves","Synthetic seed trend",
                            "8 independently sampled synthetic seeds","step","fraction",
                            uncertainty_kind="ci")
    paths=finalize_figure(fig,Path(output_dir)/"learning_curves",
                          formats=("png","pdf","svg"),contract=contract,
                          seed=17,transformations=["t-distribution 95% CI across 8 synthetic seeds"])
    return paths,issues

if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "figures")
