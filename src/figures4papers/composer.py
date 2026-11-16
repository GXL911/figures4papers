"""Compose SVG and Matplotlib panels into one physically sized paper figure."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
from io import StringIO
from math import ceil, isfinite
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import matplotlib as mpl

from .design_tokens import DEFAULT_TOKENS, DesignTokens
from .vector_export import export_svg

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _rewrite_ids(element: ET.Element, prefix: str) -> None:
    mapping = {}
    for child in element.iter():
        old = child.attrib.get("id")
        if old:
            mapping[old] = f"{prefix}-{old}"
    for child in element.iter():
        if "id" in child.attrib:
            child.set("id", mapping[child.attrib["id"]])
        for key, value in list(child.attrib.items()):
            for old, new in mapping.items():
                value = value.replace(f"url(#{old})", f"url(#{new})")
                if value == f"#{old}":
                    value = f"#{new}"
            child.set(key, value)
        if child.text:
            for old, new in mapping.items():
                child.text = child.text.replace(f"url(#{old})", f"url(#{new})")


class FigureComposer:
    """A deterministic grid composer for existing SVG or Matplotlib panels.

    The composer scales panels to fit their allocated cells; authors must still
    inspect the final physical-size proof for text density and visual balance.
    """
    def __init__(self, *, width_mm: float = 178.0, columns: int = 2,
                 panel_height_mm: float = 66.0, gap_mm: float = 5.0,
                 row_gap_mm: float = 5.0, margin_mm: float = 4.0,
                 tokens: DesignTokens = DEFAULT_TOKENS, title: str = ""):
        values = (width_mm, panel_height_mm, gap_mm, row_gap_mm, margin_mm)
        if any(not isfinite(float(v)) or float(v) <= 0 for v in values) or columns < 1 or panel_height_mm <= 10:
            raise ValueError("Composer dimensions and column count must be positive.")
        if width_mm <= 2 * margin_mm + (columns - 1) * gap_mm:
            raise ValueError("Width is too small for the requested margins and columns.")
        self.width_mm, self.columns = float(width_mm), int(columns)
        self.panel_height_mm = float(panel_height_mm)
        self.gap_mm, self.row_gap_mm = float(gap_mm), float(row_gap_mm)
        self.margin_mm = float(margin_mm)
        self.tokens, self.title = tokens, title
        self._panels: list[dict] = []

    def add_svg_panel(self, svg: str | Path, *, label: str, title: str = "") -> None:
        if not label.strip():
            raise ValueError("Every panel needs a label such as (a).")
        content = Path(svg).read_text(encoding="utf-8") if isinstance(svg, Path) else str(svg)
        root = ET.fromstring(content)
        if _local(root.tag) != "svg":
            raise ValueError("Panel content must have an SVG root.")
        view_box = root.attrib.get("viewBox")
        if not view_box:
            raise ValueError("SVG panel must declare viewBox for safe composition.")
        self._panels.append({"svg": content, "label": label, "title": title})

    def add_matplotlib_panel(self, fig, *, label: str, title: str = "") -> None:
        panel_key = f"{label}:{title}:{len(self._panels)}"
        salt = sha256(panel_key.encode("utf-8")).hexdigest()[:16]
        buffer = StringIO()
        with mpl.rc_context({"svg.hashsalt": salt, "svg.fonttype": "none"}):
            fig.savefig(buffer, format="svg", bbox_inches="tight", pad_inches=0.02)
        self.add_svg_panel(buffer.getvalue(), label=label, title=title)

    def to_svg(self) -> str:
        if not self._panels:
            raise ValueError("Cannot compose an empty figure.")
        rows = ceil(len(self._panels) / self.columns)
        title_offset = 7.0 if self.title else 0.0
        height = 2 * self.margin_mm + title_offset + rows * self.panel_height_mm + (rows - 1) * self.row_gap_mm
        panel_width = (self.width_mm - 2*self.margin_mm - (self.columns-1)*self.gap_mm) / self.columns
        root = ET.Element(f"{{{SVG_NS}}}svg", {
            "width": f"{self.width_mm:g}mm", "height": f"{height:g}mm",
            "viewBox": f"0 0 {self.width_mm:g} {height:g}", "role": "img",
            "aria-labelledby": "composed-title",
        })
        title = ET.SubElement(root, f"{{{SVG_NS}}}title", {"id": "composed-title"})
        title.text = self.title or "Composed scientific figure"
        ET.SubElement(root, f"{{{SVG_NS}}}style").text = (
            f"text{{font-family:Arial,Helvetica,sans-serif;fill:{self.tokens.foreground};}}"
        )
        ET.SubElement(root, f"{{{SVG_NS}}}rect", {
            "x": "0", "y": "0", "width": "100%", "height": "100%",
            "fill": self.tokens.background,
        })
        if self.title:
            heading = ET.SubElement(root, f"{{{SVG_NS}}}text", {
                "x": f"{self.margin_mm:g}", "y": f"{self.margin_mm+3:g}",
                "font-size": f"{9 * 25.4 / 72:g}", "data-font-size-pt": "9", "font-weight": "600",
            })
            heading.text = self.title
        top_offset = self.margin_mm + title_offset
        content_header_mm = 7.0
        for index, panel in enumerate(self._panels):
            row, col = divmod(index, self.columns)
            x = self.margin_mm + col * (panel_width + self.gap_mm)
            y = top_offset + row * (self.panel_height_mm + self.row_gap_mm)
            label = ET.SubElement(root, f"{{{SVG_NS}}}text", {
                "x": f"{x:g}", "y": f"{y+3.2:g}", "font-size": f"{self.tokens.panel_label_pt * 25.4 / 72:g}", "data-font-size-pt": f"{self.tokens.panel_label_pt:g}",
                "font-weight": "700",
            })
            label.text = panel["label"]
            if panel["title"]:
                heading = ET.SubElement(root, f"{{{SVG_NS}}}text", {
                    "x": f"{x+9:g}", "y": f"{y+3.2:g}",
                    "font-size": f"{self.tokens.title_pt * 25.4 / 72:g}", "data-font-size-pt": f"{self.tokens.title_pt:g}", "font-weight": "600",
                })
                heading.text = panel["title"]
            source = ET.fromstring(panel["svg"])
            _rewrite_ids(source, f"panel{index}")
            view_box = [float(v) for v in re.split(r"[ ,]+", source.attrib["viewBox"].strip())]
            if len(view_box) != 4 or view_box[2] <= 0 or view_box[3] <= 0:
                raise ValueError("Panel SVG has an invalid viewBox.")
            nested = ET.SubElement(root, f"{{{SVG_NS}}}svg", {
                "x": f"{x:g}", "y": f"{y+content_header_mm:g}",
                "width": f"{panel_width:g}",
                "height": f"{self.panel_height_mm-content_header_mm-1:g}",
                "viewBox": source.attrib["viewBox"],
                "preserveAspectRatio": "xMidYMid meet",
                "overflow": "hidden", "role": "img",
                "aria-label": f"{panel['label']} {panel['title']}".strip(),
            })
            for child in list(source):
                if _local(child.tag) in {"title", "desc"}:
                    continue
                nested.append(deepcopy(child))
        return ET.tostring(root, encoding="unicode")

    def export(self, out_path: str | Path, *, formats=("svg", "pdf", "png"),
               dpi: int = 300, contract=None, source_files=(), seed=None,
               transformations=()) -> list[Path]:
        return export_svg(self.to_svg(), out_path, formats=formats, dpi=dpi,
                          contract=contract, source_files=source_files,
                          seed=seed, transformations=transformations)
