"""Synthetic interval-coverage calibration; no imaginary uncertainty bands."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figures4papers import (
    FigureContract, apply_publication_style, make_reliability_diagram,
    validate_figure, finalize_figure,
)

def build(output_dir: str | Path):
    nominal=np.linspace(0.1,0.9,9)
    empirical=np.clip(nominal**1.12,0,1)  # illustrative monotonic undercoverage
    apply_publication_style()
    fig,ax=plt.subplots(figsize=(5,5))
    make_reliability_diagram(ax,nominal,empirical)
    issues=validate_figure(fig)
    contract=FigureContract("demo-reliability","reliability",
                            "Synthetic undercoverage example only",
                            "Analytical synthetic curve, no real forecasting observations",
                            "fraction","fraction")
    paths=finalize_figure(fig,Path(output_dir)/"reliability_diagram",
                          formats=("png","pdf","svg"),contract=contract,
                          transformations=["empirical = nominal ** 1.12 (synthetic)"])
    return paths,issues

if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "figures")
