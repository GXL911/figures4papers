"""Composite benchmark combining original diagrams and synthetic experiment panels."""
from pathlib import Path
from dataclasses import replace
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figures4papers import FigureContract
from figures4papers.composer import FigureComposer
from figures4papers.design_tokens import DEFAULT_TOKENS, publication_context
from figures4papers.diagram import DiagramCanvas

COMPOSITE_TOKENS = replace(DEFAULT_TOKENS, font_size_pt=8.5, axes_label_pt=8.5,
                           tick_label_pt=7.5, legend_pt=7.5, title_pt=8.5)


def _residual_svg():
    t = DEFAULT_TOKENS
    c = DiagramCanvas(80, 50, title="Residual block")
    c.add_box("x", 2, 16, 12, 10, "Input", fill="#F1F3F5", stroke=t.muted, font_size_pt=6.2)
    c.add_box("f", 19, 11, 24, 20, "Residual", subtitle="F(x)", fill="#E8F0F8", stroke=t.proposed, font_size_pt=6.2)
    c.add_circle("plus", 51, 21, 4.5, fill="#FFF4DF", stroke="#B27A26")
    c.add_text("plus-label", 51, 22, "+", font_size_pt=7, anchor="middle")
    c.add_box("y", 61, 16, 16, 10, "Output", fill="#E7F3EC", stroke=t.secondary, font_size_pt=6.2)
    c.add_arrow((14, 21), (19, 21), element_id="in")
    c.add_arrow((43, 21), (46.5, 21), element_id="fout")
    c.add_arrow((55.5, 21), (61, 21), element_id="out")
    c.add_line((8, 26), (8, 40), element_id="skip1", color=t.muted)
    c.add_line((8, 40), (51, 40), element_id="skip2", color=t.muted)
    c.add_arrow((51, 40), (51, 25.5), element_id="skip3", color=t.muted)
    c.add_text("skip-label", 29, 38, "identity shortcut", font_size_pt=6.0, color=t.muted, anchor="middle")
    return c.to_svg()


def _selective_svg():
    t = DEFAULT_TOKENS
    c = DiagramCanvas(80, 50, title="Selective state-space flow")
    items = [(2, "Input"), (21, "Project"), (40, "Δ, B, C"), (59, "Scan")]
    for i, (x, label) in enumerate(items):
        c.add_box(f"node{i}", x, 11, 17, 12, label,
                  fill=("#F1F3F5", "#E8F0F8", "#F3ECF8", "#E7F3EC")[i],
                  stroke=(t.muted, t.proposed, t.accent, t.secondary)[i], font_size_pt=6.2)
        if i:
            c.add_arrow((items[i-1][0]+17, 17), (x, 17), element_id=f"arrow{i}")
    c.add_box("sram", 5, 32, 29, 11, "SRAM", subtitle="on-chip", fill="#FFF4DF", stroke="#B27A26", font_size_pt=6.0)
    c.add_box("hbm", 46, 32, 29, 11, "HBM", subtitle="off-chip", fill="#F1F3F5", stroke=t.muted, font_size_pt=6.0)
    c.add_arrow((34, 37.5), (46, 37.5), element_id="transfer")
    return c.to_svg()


def _chart_svg():
    with publication_context(COMPOSITE_TOKENS):
        fig, ax = plt.subplots(figsize=(3.2, 1.55))
        x = np.array([1, 2, 4, 8, 16])
        a = np.array([0.58, 0.66, 0.72, 0.76, 0.78])
        b = np.array([0.55, 0.61, 0.66, 0.68, 0.69])
        ax.plot(x, a, marker="o", color=DEFAULT_TOKENS.proposed, label="Method A")
        ax.plot(x, b, marker="s", color=DEFAULT_TOKENS.baseline, label="Baseline")
        ax.set_xscale("log", base=2)
        ax.set_xticks(x, [str(int(v)) for v in x])
        ax.set_xlabel("Compute budget (synthetic)")
        ax.set_ylabel("Score")
        ax.legend(ncol=2, loc="upper left", bbox_to_anchor=(0.01, 1.02), borderaxespad=0)
        ax.grid(axis="y", color=DEFAULT_TOKENS.grid, linewidth=0.45)
        ax.set_axisbelow(True)
        fig.tight_layout()
        return fig


def build(output_dir: str | Path):
    composer = FigureComposer(width_mm=178, columns=2, panel_height_mm=65,
                              gap_mm=5, row_gap_mm=4, title="Composite scientific figure — synthetic benchmark")
    composer.add_svg_panel(_residual_svg(), label="(a)", title="Mechanism")
    composer.add_svg_panel(_selective_svg(), label="(b)", title="Selective dataflow")
    chart = _chart_svg()
    composer.add_matplotlib_panel(chart, label="(c)", title="Scaling experiment")
    # Fourth panel is a compact, explicitly synthetic matrix.
    with publication_context(COMPOSITE_TOKENS):
        fig, ax = plt.subplots(figsize=(3.2, 1.55))
        matrix = np.array([[0.72, 0.75, 0.77], [0.68, 0.73, 0.76], [0.61, 0.69, 0.74]])
        im = ax.imshow(matrix, cmap="cividis", vmin=0.6, vmax=0.8, aspect="auto")
        ax.set_xticks(range(3), ["A", "B", "C"])
        ax.set_yticks(range(3), ["Low", "Mid", "High"])
        ax.set_xlabel("Factor B")
        ax.set_ylabel("Factor A")
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{matrix[i,j]:.2f}", ha="center", va="center", fontsize=8)
        colorbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.025)
        colorbar.ax.tick_params(labelsize=7)
        fig.tight_layout(pad=0.4)
    composer.add_matplotlib_panel(fig, label="(d)", title="Ablation evidence")
    contract = FigureContract("benchmark-nature-composite", "other",
                              "Demonstrate a consistent visual system across mechanism, dataflow and evidence panels",
                              "Original diagrams and synthetic teaching data; not a reproduction of a Nature paper",
                              "panel", "mixed units",
                              provenance_note="Panels are illustrative and intentionally use synthetic values.")
    paths = composer.export(Path(output_dir) / "05_nature_style_composite",
                            formats=("svg", "pdf", "png"), contract=contract,
                            transformations=["compose two original SVG diagrams and two synthetic Matplotlib panels",
                                             "place in a 2x2 grid at 178 mm total width"])
    plt.close(chart); plt.close(fig)
    return paths, []


if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "generated")
