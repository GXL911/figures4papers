"""Compact seed-1 MACL retention plots with explicit cohort sizes and units."""
from __future__ import annotations

import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from figures4papers import FigureContract, FigureStyle, apply_publication_style, finalize_figure
from figures4papers.figure_validation import validate_line_artist
from figures4papers.layout_review import review_layout

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "figure_MACL"
SCENARIOS = (
    ("sub", "MedMCQA disciplines", "Accuracy change (pp)"),
    ("qa", "Medical QA datasets", "Accuracy change (pp)"),
    ("task", "Heterogeneous medical tasks", "Mean score change (0–100 scale)"),
)
METHODS = {
    "Sequential SFT": ("Sequential SFT", "#555555", "--", "o"),
    "Replay": ("Replay", "#257450", "-.", "s"),
    "MACL-prev": ("MACL", "#0F4D92", "-", "^"),
}
WIDTH_MM = 178


def load_script(name):
    path = SOURCE / f"{name}.py"
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def retention_cohorts(scores):
    """Rows are training stages. For each offset use only tasks observed at that offset."""
    matrix = np.asarray(scores, dtype=float)
    if matrix.ndim != 2 or min(matrix.shape) == 0 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Expected a nonempty square stage-by-task matrix.")
    if not np.isfinite(matrix).all() or (matrix < 0).any() or (matrix > 100).any():
        raise ValueError("Expected finite scores on the original 0–100 scale.")
    n = len(matrix)
    return [np.array([matrix[k + d, k] - matrix[k, k] for k in range(n - d)])
            for d in range(n)]


def build_figure():
    apply_publication_style(FigureStyle(font_size=7.3, axes_linewidth=.6))
    fig, axes = plt.subplots(1, 3, sharey=True, figsize=(WIDTH_MM / 25.4, 2.58))
    fig.subplots_adjust(left=.075, right=.974, bottom=.27, top=.72, wspace=.31)
    overview = load_script("plot_overview")
    records = {}
    for i, (ax, (tag, title, unit)) in enumerate(zip(axes, SCENARIOS)):
        module = load_script(f"plot_exp_{tag}")
        records[tag] = {}
        for name, (label, color, linestyle, marker) in METHODS.items():
            scores = module.RESULTS[name]
            parts = retention_cohorts(scores)
            values = np.array([p.mean() for p in parts])
            np.testing.assert_allclose(values, overview.retention_curve(scores), atol=1e-12, rtol=0)
            x = np.arange(len(values))
            line, = ax.plot(x, values, label=label, color=color, linestyle=linestyle,
                            marker=marker, markersize=2.8, linewidth=1.0)
            validate_line_artist(line, x, values)
            records[tag][name] = {"mean_change": values.tolist(), "task_count": [len(p) for p in parts]}
        # Show individual numeric series without clipping outliers from the source.
        ax.axhline(0, color="#969696", linewidth=.65, zorder=0)
        ax.set_title(title, fontsize=7.5, weight="bold", pad=6)
        ax.set_xlabel("Subsequent tasks learned", fontsize=6.7)
        ax.set_xticks(sorted({0, (len(x)-1)//2, len(x)-1}))
        ax.tick_params(labelsize=6.5, length=2.2, pad=2)
        ax.grid(axis="y", linewidth=.45, alpha=.2)
        if i == 0:
            ax.set_ylabel("Score change (points)", fontsize=6.7)
        ax.text(.5, -.39, f"{unit} • {len(x)} to 1 tasks", transform=ax.transAxes,
                ha="center", fontsize=6.1)
    fig.text(.03, .965, "MACL · Retention after learning a task", va="top", fontsize=9.5, weight="bold")
    handles = [Line2D([], [], label=label, color=color, linestyle=ls, marker=marker,
                      linewidth=1, markersize=3) for label, color, ls, marker in METHODS.values()]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(.016, .894), ncols=3,
               borderaxespad=.1, fontsize=6.7, handlelength=2.5)
    fig.text(.03, .026, "Seed 1 only. Each point averages the tasks still observable at that offset, with no uncertainty band.",
             fontsize=6.4)
    return fig, records


def render(out):
    out.mkdir(parents=True, exist_ok=True)
    with matplotlib.rc_context():
        fig, records = build_figure()
        audit = review_layout(fig, width_mm=WIDTH_MM)
        if any(audit[k] for k in ("small_text", "outside_canvas", "text_overlap_candidates")):
            plt.close(fig)
            raise RuntimeError(f"MACL layout QA failed: {audit}")
        cohort_path = out / "retention-cohorts.json"
        cohort_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
        finalize_figure(
            fig, out / "retention", crop=False, formats=("png", "pdf", "svg"),
            contract=FigureContract(
                "macl-retention-seed1", "learning_curves", "Retention averages for three scenarios, conditional on offset.",
                "figure_MACL/plot_overview.py and the three plot_exp_* seed-1 arrays",
                "subsequent tasks learned", "points on each original 0–100 task score",
                provenance_note="No error bars. The heterogeneous panel averages accuracy, ROUGE-L and micro-F1 "
                                "changes equally by task; it is not an accuracy statistic.",
            ),
            source_files=[Path(__file__), SOURCE / "plot_overview.py",
                          *(SOURCE / f"plot_exp_{tag}.py" for tag, _, _ in SCENARIOS), cohort_path],
            seed=1,
            transformations=[
                "Compute mean of R[k+d,k]-R[k,k] over k < T-d; record the changing cohort sizes.",
                "Match original overview means for Sequential SFT, Replay and MACL; omit task-level lines in this layout.",
            ],
        )
    (out / "layout.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "review/generated/macl")
    render(parser.parse_args().out)
