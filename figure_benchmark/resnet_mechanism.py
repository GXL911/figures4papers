"""ResNet-inspired residual-learning diagram using original synthetic artwork."""
from pathlib import Path
from figures4papers import FigureContract
from figures4papers.diagram import DiagramCanvas
from figures4papers.design_tokens import DEFAULT_TOKENS
from figures4papers.vector_export import export_svg


def build(output_dir: str | Path):
    t = DEFAULT_TOKENS
    c = DiagramCanvas(178, 82, title="Residual learning mechanism",
                      description="Original explanatory diagram of identity shortcut plus residual branch.")
    c.add_text("caption", 4, 9, "Residual block", font_size_pt=10, weight="700")
    c.add_box("input", 4, 30, 25, 16, "Input", subtitle="x", fill="#F1F3F5", stroke=t.muted)
    c.add_box("residual", 43, 17, 47, 42, "Residual function", subtitle="Conv → BN → ReLU → Conv", fill="#E8F0F8", stroke=t.proposed, font_size_pt=7.5)
    c.add_circle("sum", 107, 38, 7.5, fill="#FFF4DF", stroke="#B27A26", label="+")
    c.add_box("output", 129, 30, 27, 16, "Output", subtitle="y", fill="#E7F3EC", stroke=t.secondary)
    c.add_arrow((29, 38), (43, 38), color=t.proposed, element_id="main-in")
    c.add_arrow((90, 38), (99, 38), color=t.proposed, element_id="residual-out")
    c.add_arrow((115, 38), (129, 38), color=t.secondary, element_id="sum-out")
    c.add_line((16.5, 46), (16.5, 68), color=t.muted, element_id="shortcut-down")
    c.add_line((16.5, 68), (107, 68), color=t.muted, element_id="shortcut-horizontal")
    c.add_arrow((107, 68), (107, 46), color=t.muted, element_id="shortcut-up")
    c.add_text("shortcut-label", 60, 65, "Identity shortcut", font_size_pt=7, color=t.muted, anchor="middle")
    c.add_text("equation", 80, 79, "y = F(x) + x", font_size_pt=9, weight="700", anchor="middle")
    contract = FigureContract("benchmark-resnet-mechanism", "other",
                              "The identity path is added to the learned residual function",
                              "Original explanatory vector diagram; no paper artwork copied",
                              "not applicable", "not applicable",
                              provenance_note="Conceptual diagram; it omits implementation-specific projection shortcuts.")
    paths = export_svg(c.to_svg(), Path(output_dir) / "01_resnet_mechanism",
                       formats=("svg", "pdf", "png"), contract=contract,
                       transformations=["construct original vector diagram from reusable SVG primitives"])
    return paths, []


if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "generated")
