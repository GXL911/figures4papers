"""Non-destructive adapters for three upstream case-study datasets.

These read original script-encoded values but do NOT independently verify
scientific claims, error-bar definitions or original paper figures.
The original figure_* scripts and figures remain untouched.
"""
from __future__ import annotations
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figures4papers import (
    FigureContract, apply_publication_style, finalize_figure,
    make_grouped_bar, make_learning_curves, make_heatmap,
    validate_figure, validate_bar_artists, validate_line_artist,
)

ROOT=Path(__file__).resolve().parents[1]

def _load_source(path: Path, name: str):
    spec=spec_from_file_location(name,path)
    module=module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    spec.loader.exec_module(module)
    return module

def immunostruct_means(output_dir: Path):
    """Replot IEDB means only: original error-bar semantics need paper verification."""
    path=ROOT/"figure_ImmunoStruct"/"raw_data.py"
    original=ROOT/"figure_ImmunoStruct"/"plot_bars.py"
    data=_load_source(path,"legacy_immunostruct").data_comparison_IEDB
    means=np.asarray(data["mean"],dtype=float)  # method x metric
    apply_publication_style()
    fig,ax=plt.subplots(figsize=(12,5))
    bars=make_grouped_bar(ax,data["metrics"],means,data["methods"],
                          colors=data["colors"],ylabel="Score (fraction)")
    for i,container in enumerate(bars):
        validate_bar_artists(container,means[i])
    ax.set_xlabel("Metric")
    ax.set_ylim(0,1.0)
    ax.legend(loc="upper center",bbox_to_anchor=(0.5,-0.22),ncol=3,fontsize=8)
    fig.subplots_adjust(bottom=0.34)
    issues=validate_figure(fig)
    contract=FigureContract(
        figure_id="legacy-immunostruct-iedb-means",
        chart_type="grouped_bar",
        takeaway="Original script-encoded IEDB comparison means, no uncertainty claims",
        source_description=str(path.relative_to(ROOT)),
        x_unit="metric",y_unit="fraction",uncertainty_kind="none",
        provenance_note="Mean only: original std arrays mix /sqrt(5); uncertainty withheld pending source verification.")
    paths=finalize_figure(fig,output_dir/"immunostruct_means",formats=("png","pdf","svg"),
                          contract=contract,source_files=[path,original],
                          transformations=["Read original data_comparison_IEDB['mean']; draw each method unchanged"])
    return paths,issues

def macl_retention_example(output_dir: Path):
    """A two-method, one-task slice from the original MACL six-task accuracy matrix."""
    path=ROOT/"figure_MACL"/"plot_exp_qa.py"
    data=_load_source(path,"legacy_macl")
    x=np.arange(1,len(data.STAGE_LABELS)+1)
    methods=["MACL-prev","Sequential SFT"]
    scores=np.stack([data.RESULTS[m][:,0] for m in methods])
    apply_publication_style()
    fig,ax=plt.subplots(figsize=(7,4))
    lines=make_learning_curves(ax,x,scores,["MACL","Sequential SFT"],
                              xlabel="Sequential training stage",
                              ylabel="PubMedQA accuracy (%)")
    for i,line in enumerate(lines):
        validate_line_artist(line,x,scores[i])
    ax.set_xticks(x)
    ax.set_ylim(0,100)
    issues=validate_figure(fig)
    contract=FigureContract(
        figure_id="legacy-macl-pubmedqa",
        chart_type="learning_curves",
        takeaway="Single-run PubMedQA retention over subsequent tasks",
        source_description=str(path.relative_to(ROOT)),
        x_unit="training stage",y_unit="accuracy (%)",
        uncertainty_kind="none",
        provenance_note="Original script documents Seed 1 only; no uncertainty band is inferred.")
    paths=finalize_figure(fig,output_dir/"macl_pubmedqa",formats=("png","pdf","svg"),
                          contract=contract,source_files=[path],
                          transformations=["Take first task column from two training-stage x task matrices"])
    return paths,issues

def rnagenscape_heatmap_example(output_dir: Path):
    """Visualize a subset of the original encoded optimization success-rate arrays."""
    path=ROOT/"figure_RNAGenScape"/"plot_comparison.py"
    data=_load_source(path,"legacy_rnagenscape")
    values=np.stack([
        data.results_openvaccine_pct_pos,
        data.results_zebrafish_pct_pos,
        data.results_ribosome_pct_pos,
    ],axis=1)
    names=data.options[:-1]  # the final label is a derived improvement row
    if len(names)!=values.shape[0]:
        raise ValueError("Legacy method labels mismatch their 13 rows.")
    apply_publication_style()
    fig,ax=plt.subplots(figsize=(8,8))
    image=make_heatmap(ax,values,
            x_labels=["OpenVaccine (+)","Zebrafish (+)","Ribosome (+)"],
            y_labels=names,cmap="Blues",cbar_label="Success rate (%)",
            annotate=True,vmin=0,vmax=100)
    np.testing.assert_allclose(np.asarray(image.get_array()),values)
    ax.set(xlabel="Property benchmark",ylabel="Original method")
    ax.tick_params(axis="y",labelsize=8)
    issues=validate_figure(fig)
    contract=FigureContract(
        figure_id="legacy-rnagenscape-success",
        chart_type="heatmap",
        takeaway="Original script-encoded success-rate subset (not re-measured)",
        source_description=str(path.relative_to(ROOT)),
        x_unit="benchmark",y_unit="method",
        uncertainty_kind="none",
        provenance_note="Original script values; no independent paper-data audit.")
    paths=finalize_figure(fig,output_dir/"rnagenscape_success",formats=("png","pdf","svg"),
                          contract=contract,source_files=[path],
                          transformations=["Stack three original positive-optimization percentage arrays as columns"])
    return paths,issues

def run_all(output_dir: Path):
    output_dir=Path(output_dir)
    return {
        "immunostruct_means": immunostruct_means(output_dir),
        "macl_pubmedqa": macl_retention_example(output_dir),
        "rnagenscape_success": rnagenscape_heatmap_example(output_dir),
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=ROOT/"examples"/"legacy-generated")
    args=parser.parse_args()
    for name,(paths,issues) in run_all(args.out).items():
        print(f"{name}: {len(paths)} exported figures; {len(issues)} warnings")
        for issue in issues:
            print(f"  {issue.code}: {issue.message}")
