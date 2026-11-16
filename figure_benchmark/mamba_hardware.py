"""Selective-SSM and hardware dataflow concept diagram; not a Mamba reproduction."""
from pathlib import Path
from figures4papers import FigureContract
from figures4papers.diagram import DiagramCanvas
from figures4papers.design_tokens import DEFAULT_TOKENS
from figures4papers.vector_export import export_svg


def build(output_dir: str | Path):
    t = DEFAULT_TOKENS
    c = DiagramCanvas(178, 94, title="Input-dependent state-space computation",
                      description="Conceptual dataflow diagram separating selection, scan and memory hierarchy.")
    c.add_text("heading", 5, 9, "Selective state-space dataflow", font_size_pt=10, weight="700")
    c.add_box("tokens", 5, 25, 25, 17, "Input", subtitle="sequence x", fill="#F1F3F5", stroke=t.muted)
    c.add_box("projection", 39, 25, 35, 17, "Projection", subtitle="input-dependent", fill="#E8F0F8", stroke=t.proposed)
    c.add_box("parameters", 83, 18, 39, 31, "Selective parameters", subtitle="Δ(x), B(x), C(x)", fill="#F3ECF8", stroke=t.accent)
    c.add_box("scan", 132, 25, 39, 17, "Selective scan", subtitle="state update", fill="#E7F3EC", stroke=t.secondary)
    c.add_arrow((30, 33.5), (39, 33.5), element_id="input-to-projection")
    c.add_arrow((74, 33.5), (83, 33.5), element_id="projection-to-parameters")
    c.add_arrow((122, 33.5), (132, 33.5), element_id="parameters-to-scan")
    c.add_text("hardware-label", 5, 61, "Hardware-aware execution (conceptual)", font_size_pt=8, weight="700")
    c.add_box("sram", 15, 68, 62, 17, "On-chip SRAM", subtitle="fast, limited capacity", fill="#FFF4DF", stroke="#B27A26")
    c.add_box("hbm", 101, 68, 62, 17, "Off-chip HBM", subtitle="larger, higher latency", fill="#F1F3F5", stroke=t.muted)
    c.add_arrow((77, 76.5), (101, 76.5), label="data movement", color=t.baseline, element_id="memory-transfer")
    c.add_text("note", 89, 55, "Avoid materializing the full time-varying state-space tensors", font_size_pt=6.5,
               color=t.muted, anchor="middle")
    contract = FigureContract("benchmark-selective-ssm-hardware", "other",
                              "Selection makes state-space parameters input-dependent; execution must manage data movement",
                              "Original conceptual vector diagram; not copied from the Mamba paper",
                              "sequence position", "state / memory traffic",
                              provenance_note="Simplified explanatory view; it is not a complete implementation or kernel schedule.")
    paths = export_svg(c.to_svg(), Path(output_dir) / "03_selective_ssm_hardware",
                       formats=("svg", "pdf", "png"), contract=contract,
                       transformations=["construct original vector dataflow diagram from reusable SVG primitives"])
    return paths, []


if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "generated")
