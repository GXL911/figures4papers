import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import pytest

from figures4papers import FigureContract
from figures4papers.composer import FigureComposer
from figures4papers.design_tokens import (
    DEFAULT_TOKENS, DOUBLE_COLUMN, SINGLE_COLUMN, publication_context,
)
from figures4papers.diagram import DiagramCanvas
from figures4papers.visual_qa import audit_palette, audit_svg, contrast_ratio


def test_physical_presets_and_rc_context_isolation():
    assert SINGLE_COLUMN.width_mm == 89
    assert DOUBLE_COLUMN.width_mm == 178
    before = matplotlib.rcParams["font.size"]
    with publication_context():
        assert matplotlib.rcParams["font.size"] == DEFAULT_TOKENS.font_size_pt
    assert matplotlib.rcParams["font.size"] == before


def test_diagram_geometry_ids_and_svg_qa():
    canvas = DiagramCanvas(80, 50, title="Test mechanism", description="A simple dataflow")
    canvas.add_box("input", 3, 15, 18, 14, "Input", font_size_pt=7)
    canvas.add_box("operator", 42, 15, 30, 14, "Operator", font_size_pt=7)
    canvas.add_arrow((21, 22), (42, 22), element_id="input-to-operator")
    svg = canvas.to_svg()
    ET.fromstring(svg)
    report = audit_svg(svg, min_font_pt=6)
    assert report["has_title"] and report["has_role"] and report["has_viewBox"]
    assert report["duplicate_ids"] == []
    assert "small_text" not in report["issues"]
    with pytest.raises(ValueError):
        canvas.add_box("input", 2, 2, 5, 5, "Duplicate")
    with pytest.raises(ValueError):
        canvas.add_box("outside", 78, 2, 5, 5, "Outside")


def test_composer_prefixes_svg_ids_and_exports(tmp_path):
    def diagram():
        canvas = DiagramCanvas(40, 30, title="Panel")
        canvas.add_box("same-node", 3, 8, 15, 12, "Node", font_size_pt=7)
        return canvas.to_svg()

    composer = FigureComposer(width_mm=178, columns=2, panel_height_mm=55, title="Test composite")
    composer.add_svg_panel(diagram(), label="(a)", title="First")
    composer.add_svg_panel(diagram(), label="(b)", title="Second")
    fig, ax = plt.subplots(figsize=(2.5, 1.4))
    ax.plot([0, 1, 2], [0.2, 0.5, 0.8])
    ax.set_xlabel("Step")
    ax.set_ylabel("Score")
    composer.add_matplotlib_panel(fig, label="(c)", title="Data")
    svg = composer.to_svg()
    root = ET.fromstring(svg)
    ids = [el.attrib["id"] for el in root.iter() if "id" in el.attrib]
    assert len(ids) == len(set(ids))
    assert root.attrib["width"] == "178mm"
    report = audit_svg(svg, min_font_pt=6)
    assert report["duplicate_ids"] == []
    contract = FigureContract("composer-test", "other", "Compose panels", "Synthetic fixture",
                              "panel", "mixed")
    paths = composer.export(tmp_path / "composed", formats=("svg", "pdf", "png"), contract=contract)
    assert {p.suffix for p in paths} == {".svg", ".pdf", ".png"}
    assert all(p.is_file() and p.stat().st_size > 100 for p in paths)
    assert (tmp_path / "composed.manifest.json").is_file()
    plt.close(fig)


def test_palette_contrast_screening():
    assert contrast_ratio("#20242A", "#FFFFFF") > 10
    result = audit_palette({"body": "#20242A", "muted": "#68717D"})
    assert result["low_text_contrast"] == []
