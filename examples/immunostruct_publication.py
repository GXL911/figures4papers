"""Publication-width adaptations of four aggregate ImmunoStruct figure panels."""
from __future__ import annotations

import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from figures4papers import FigureContract, FigureStyle, apply_publication_style, finalize_figure
from figures4papers.layout_review import review_layout
from figures4papers.figure_validation import validate_line_artist

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "figure_ImmunoStruct/raw_data.py"
ORIGINAL = ROOT / "figure_ImmunoStruct/plot_bars.py"
PAPER = "https://doi.org/10.1038/s42256-025-01163-y"
WIDTH_MM = 178
METRIC_KINDS = {"AUROC": "sd", "AUPRC": "sd", "Mean PPVn": "sem"}
PANELS = {
    "iedb_comparison": ("data_comparison_IEDB", "IEDB", "comparison", "Fig. 3a"),
    "iedb_ablation": ("data_ablation_IEDB", "IEDB", "ablation", "Fig. 3b"),
    "cedar_comparison": ("data_comparison_Cancer", "CEDAR", "comparison", "Fig. 4a"),
    "cedar_ablation": ("data_ablation_Cancer", "CEDAR", "ablation", "Fig. 4b"),
}


def load_aggregate_data():
    spec = spec_from_file_location("immunostruct_aggregate", DATA)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def panel_data(key):
    attr, dataset, task, paper_panel = PANELS[key]
    data = getattr(load_aggregate_data(), attr)
    metrics = data["metrics"]
    if list(METRIC_KINDS) != metrics:
        raise ValueError(f"Uncertainty mapping needs re-audit: {metrics}")
    if task == "comparison":
        indices = list(range(len(data["methods"])))
        labels = [m.replace(r"$_\text{retrained}$", " (retrained)").replace(" (ours)", "")
                  for m in data["methods"]]
    elif dataset == "IEDB":
        indices = list(range(len(data["ablations"])))
        short = ["Structure", "Sequence", "Biochem.", "MMA", "Transfer"]
        if data["components"] != ["Structure", "Sequence", "Bchems", "MMA", "Transfer Learning"]:
            raise ValueError("Ablation components need re-audit.")
        labels = [" + ".join(s for s, present in zip(short, mask) if present == "1")
                  for mask in data["ablations"]]
    else:
        indices = [6, 4, 0]  # exactly the three rows in the original plotted CEDAR subset
        if [data["coeffs"][i] for i in indices] != [[True, 0.01], [True, 0], [False, 0]]:
            raise ValueError("CEDAR ablation rows need re-audit.")
        labels = ["Transfer + contrastive", "Transfer only", "Neither component"]
    means, halfwidth = data["mean"][indices], data["std"][indices]
    if not (means.shape == halfwidth.shape == (len(labels), len(metrics))
            and np.isfinite(means).all() and np.isfinite(halfwidth).all()
            and (halfwidth >= 0).all() and ((means >= 0) & (means <= 1)).all()):
        raise ValueError(f"Invalid aggregates for {key}.")
    return dataset, task, paper_panel, labels, indices, metrics, means, halfwidth


def build_figure(key):
    dataset, task, panel, labels, indices, metrics, means, halfwidth = panel_data(key)
    apply_publication_style(FigureStyle(font_size=7.4, axes_linewidth=0.6))
    width = WIDTH_MM / 25.4
    fig, axes = plt.subplots(1, 3, sharey=True, figsize=(width, 1.36 + 0.165 * len(labels)))
    fig.subplots_adjust(left=.375 if key == "iedb_ablation" else .27, right=.979,
                        top=.77 if len(labels) < 5 else .85,
                        bottom=.29 if len(labels) < 5 else .21, wspace=.28)
    fig.text(.025, .95, f"{dataset} · {task.title()}", fontsize=9.5, weight="bold", va="top")
    fig.text(.025, .025, "Points are means. Whiskers retain the paper's metric-specific SD or SEM (n = 5).",
             fontsize=6.4)
    y = np.arange(len(labels))
    for i, (ax, metric) in enumerate(zip(axes, metrics)):
        group = ax.errorbar(means[:, i], y, xerr=halfwidth[:, i], fmt="o", markersize=3,
                            capsize=1.7, color="#0F4D92", elinewidth=.9)
        validate_line_artist(group.lines[0], means[:, i], y)
        expected = np.stack([
            np.column_stack((means[:, i] - halfwidth[:, i], y)),
            np.column_stack((means[:, i] + halfwidth[:, i], y)),
        ], axis=1)
        np.testing.assert_allclose(group.lines[2][0].get_segments(), expected, rtol=0, atol=1e-12)
        ax.set_title(f"{metric} · {METRIC_KINDS[metric].upper()}", fontsize=7.5, pad=5)
        lower = max(0, (np.floor(np.min(means[:, i] - halfwidth[:, i]) * 10) - .25) / 10)
        upper = min(1, (np.ceil(np.max(means[:, i] + halfwidth[:, i]) * 10) + .25) / 10)
        ax.set_xlim(lower, upper)
        ax.set_xlabel("Score (fraction)", fontsize=6.7, labelpad=3)
        ax.locator_params(axis="x", nbins=3)
        ax.grid(True, axis="x", alpha=.22, linewidth=.45)
        ax.tick_params(axis="both", labelsize=6.7, length=2, pad=2)
        if i != 0:
            ax.tick_params(axis="y", left=False)
    axes[0].set_yticks(y, labels)
    axes[0].set_ylim(len(labels)-.55, -.45)
    return fig


def render_all(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    with matplotlib.rc_context({"svg.hashsalt": "figures4papers-immunostruct"}):
        for key, (_, dataset, task, paper_panel) in PANELS.items():
            fig = build_figure(key)
            contract = FigureContract(
                figure_id=f"immunostruct-{key.replace('_', '-')}", chart_type="other",
                takeaway=f"Script-encoded {dataset} {task} means and metric-specific whiskers.",
                source_description=f"ImmunoStruct {paper_panel}: {PAPER}; figure_ImmunoStruct/raw_data.py",
                x_unit="score (fraction)", y_unit="method or ablation",
                uncertainty_kind="mixed", uncertainty_by_metric=METRIC_KINDS,
                provenance_note="Paper captions identify sample SD for AUROC/AUPRC and SEM for Mean PPVn (five reported experiments). "
                                "The raw_data.py third column is already divided by sqrt(5); no second division. "
                                "Run-level data were not independently recomputed.",
            )
            audit = review_layout(fig, width_mm=WIDTH_MM)
            if audit["small_text"] or audit["outside_canvas"] or audit["text_overlap_candidates"]:
                plt.close(fig)
                raise RuntimeError(f"{key} failed layout QA: {audit}")
            paths = finalize_figure(
                fig, out / key, formats=("png", "pdf", "svg"), crop=False, contract=contract,
                source_files=[DATA, ORIGINAL, Path(__file__)],
                transformations=[
                    "Replace truncated bars with centered dots, retaining signed endpoints and categorical order.",
                    "Display exactly the original plotted rows; CEDAR ablation uses indices [6, 4, 0].",
                    "Preserve the already encoded metric-specific whisker magnitudes unchanged.",
                ],
            )
            results[key] = {"outputs": [p.name for p in paths], "layout": audit}
    (out / "layout.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "review/generated/immunostruct")
    args = parser.parse_args()
    print(f"Rendered {len(render_all(args.out))} ImmunoStruct publication-width figures")
