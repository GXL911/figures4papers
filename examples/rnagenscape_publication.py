"""Plot only checked-in aggregate benchmark tables, with explicit color semantics."""
from __future__ import annotations

import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np

from figures4papers import FigureContract, FigureStyle, apply_publication_style, finalize_figure
from figures4papers.layout_review import review_layout

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "figure_RNAGenScape/plot_comparison.py"
WIDTH_MM = 178
DATASETS = ("openvaccine", "zebrafish", "ribosome")
DIRECTIONS = ("pos", "neg")
TITLES = {"pct": "Success rate (%)", "delta": "Median signed property change"}
TICK_LABELS = ("OpenVaccine +", "OpenVaccine −", "Zebrafish +", "Zebrafish −", "Ribosome +", "Ribosome −")


def load_table(metric):
    if metric not in TITLES:
        raise ValueError("Expected 'pct' or 'delta'.")
    spec = spec_from_file_location("rnagenscape_aggregates", SOURCE)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    # Original options end with a derived relative-improvement row, not an evaluated method.
    if "Improvement" not in module.options[-1]:
        raise ValueError("Expected a derived final row in original options.")
    labels = [s if "RNAGenScape" not in s else "RNAGenScape" for s in module.options[:-1]]
    data = np.column_stack([getattr(module, f"results_{d}_{metric}_{s}")
                            for d in DATASETS for s in DIRECTIONS])
    if data.shape != (len(labels), len(TICK_LABELS)) or not np.isfinite(data).all():
        raise ValueError("Unexpected benchmark aggregate table.")
    if metric == "pct" and not ((data >= 0) & (data <= 100)).all():
        raise ValueError("Success rates must be percentages.")
    return labels, data


def render(out):
    out.mkdir(parents=True, exist_ok=True)
    audits = {}
    with matplotlib.rc_context():
        for metric, title in TITLES.items():
            labels, values = load_table(metric)
            apply_publication_style(FigureStyle(font_size=7, axes_linewidth=.6))
            fig = plt.figure(figsize=(WIDTH_MM / 25.4, 3.37))
            ax = fig.add_axes([.269, .15, .68, .64])
            cax = fig.add_axes([.269, .066, .58, .030])
            if metric == "pct":
                image = ax.imshow(values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
            else:
                bound = float(np.abs(values).max())
                image = ax.imshow(values, cmap="RdBu", norm=TwoSlopeNorm(0, -bound, bound), aspect="auto")
            np.testing.assert_array_equal(np.asarray(image.get_array()), values)
            for (i, j), value in np.ndenumerate(values):
                rgba = image.cmap(image.norm(value))
                luminance = np.dot(rgba[:3], [.299, .587, .114])
                label = f"{value:.1f}" if metric == "pct" else f"{value:+.2f}"
                ax.text(j, i, label, ha="center", va="center", fontsize=6.2,
                        color="black" if luminance >= .55 else "white")
            ax.set_yticks(list(range(len(labels))), labels=labels)
            ax.set_xticks(range(len(TICK_LABELS)), labels=TICK_LABELS)
            ax.xaxis.tick_top()
            ax.tick_params(axis="both", length=0, pad=3, labelsize=6.5)
            for spine in ax.spines.values():
                spine.set_visible(False)
            cbar = fig.colorbar(image, cax=cax, orientation="horizontal")
            cbar.ax.tick_params(labelsize=6.2, length=2, pad=2)
            if metric == "pct":
                cbar.set_ticks([0, 25, 50, 75, 100])
            else:
                cbar.set_ticks([-2, -1, 0, 1, 2])
            fig.text(.029, .966, f"RNAGenScape · {title}", va="top", fontsize=9.5, weight="bold")
            note = ("Common color scale from 0 to 100%." if metric == "pct"
                    else "Color shows sign and magnitude, not desirability. Compare scores within each benchmark.")
            fig.text(.029, .899, f"{note} Column signs indicate the target direction.", va="top", fontsize=6.4)
            key = "success_rate" if metric == "pct" else "median_change"
            audit = review_layout(fig, width_mm=WIDTH_MM)
            if any(audit[k] for k in ("small_text", "outside_canvas", "text_overlap_candidates")):
                plt.close(fig)
                raise RuntimeError(f"{key} layout QA failed: {audit}")
            audits[key] = audit
            finalize_figure(
                fig, out / key, crop=False, formats=("png", "pdf", "svg"),
                contract=FigureContract(
                    f"rnagenscape-{key.replace('_', '-')}", "heatmap",
                    f"Original script-encoded 13-method aggregate table: {title}.",
                    "figure_RNAGenScape/plot_comparison.py", "benchmark and target direction", "method",
                    provenance_note="Descriptive aggregate display. No sequence-level inputs or independent recomputation. "
                                    "The scale of a signed property change is not a cross-benchmark efficacy comparison.",
                ),
                source_files=[SOURCE, Path(__file__)],
                transformations=[
                    "Retain all 13 method rows and 6 benchmark-direction columns, without changing values.",
                    "Separate median change and success rate, and replace column-specific color limits with one declared scale per chart.",
                    "Do not carry over the derived relative-improvement row or mix percentages with percentage points.",
                ],
            )
    (out / "layout.json").write_text(json.dumps(audits, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "review/generated/rnagenscape")
    render(parser.parse_args().out)
