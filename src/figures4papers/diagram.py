"""Small dependency-light SVG engine for scientific mechanism diagrams.

Coordinates are millimetres on the final page. Text sizes are points. The
engine intentionally provides primitives rather than trying to infer a diagram
from prose; authors remain responsible for the scientific meaning and layout.
"""
from __future__ import annotations
from dataclasses import dataclass
from html import escape
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from matplotlib.colors import is_color_like, to_hex

from .design_tokens import DEFAULT_TOKENS, DesignTokens

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def _num(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


def _color(value: str) -> str:
    if value == "none":
        return value
    if not is_color_like(value):
        raise ValueError(f"Invalid SVG color: {value!r}")
    return to_hex(value, keep_alpha=True)


@dataclass(frozen=True)
class DiagramNode:
    node_id: str
    x: float
    y: float
    width: float
    height: float


class DiagramCanvas:
    def __init__(self, width_mm: float, height_mm: float, *, title: str,
                 description: str = "", tokens: DesignTokens = DEFAULT_TOKENS):
        self.width_mm = _num(width_mm, "width_mm")
        self.height_mm = _num(height_mm, "height_mm")
        if self.width_mm <= 0 or self.height_mm <= 0:
            raise ValueError("Canvas dimensions must be positive.")
        if not title.strip():
            raise ValueError("A diagram needs a nonblank title.")
        self.title = title
        self.description = description
        self.tokens = tokens
        self._elements: list[str] = []
        self._ids: set[str] = set()
        self._arrow_count = 0

    def _claim_id(self, element_id: str) -> str:
        if not element_id or element_id in self._ids:
            raise ValueError(f"Element id must be unique and nonblank: {element_id!r}")
        self._ids.add(element_id)
        return escape(element_id, quote=True)

    def _inside(self, x: float, y: float) -> None:
        if not (0 <= x <= self.width_mm and 0 <= y <= self.height_mm):
            raise ValueError("Element coordinate falls outside the diagram canvas.")

    def add_box(self, node_id: str, x: float, y: float, width: float, height: float,
                label: str, *, subtitle: str = "", fill: str = "#EAF1F7",
                stroke: str | None = None, radius: float = 2.0,
                label_color: str | None = None, font_size_pt: float = 8.0) -> DiagramNode:
        x, y, width, height = (_num(v, n) for v, n in
                               ((x, "x"), (y, "y"), (width, "width"), (height, "height")))
        radius = _num(radius, "radius")
        font_size_pt = _num(font_size_pt, "font_size_pt")
        if width <= 0 or height <= 0 or radius < 0 or font_size_pt <= 0:
            raise ValueError("Box dimensions, radius and font size are invalid.")
        self._inside(x, y)
        self._inside(x + width, y + height)
        element_id = self._claim_id(node_id)
        fill, stroke = _color(fill), _color(stroke or self.tokens.proposed)
        text_color = _color(label_color or self.tokens.foreground)
        self._elements.append(
            f'<rect id="{element_id}" x="{x:g}" y="{y:g}" width="{width:g}" '
            f'height="{height:g}" rx="{radius:g}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="0.28" />'
        )
        lines = [str(label)] + ([str(subtitle)] if subtitle else [])
        line_height = max(3.3, font_size_pt * 0.42)
        start_y = y + height / 2 - (len(lines) - 1) * line_height / 2 + font_size_pt * 0.12
        for index, line in enumerate(lines):
            weight = "600" if index == 0 else "400"
            size = font_size_pt if index == 0 else max(6.0, font_size_pt - 1.0)
            self._elements.append(
                f'<text x="{x + width/2:g}" y="{start_y + index*line_height:g}" '
                f'text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
                f'font-size="{size * 25.4 / 72:g}" data-font-size-pt="{size:g}" font-weight="{weight}" fill="{text_color}">'
                f'{escape(line)}</text>'
            )
        return DiagramNode(node_id, x, y, width, height)

    def add_text(self, element_id: str, x: float, y: float, text: str, *,
                 font_size_pt: float = 8.0, color: str | None = None,
                 weight: str = "400", anchor: str = "start") -> None:
        x, y = _num(x, "x"), _num(y, "y")
        self._inside(x, y)
        font_size_pt = _num(font_size_pt, "font_size_pt")
        if font_size_pt <= 0 or anchor not in {"start", "middle", "end"}:
            raise ValueError("Invalid text size or anchor.")
        if weight not in {"400", "500", "600", "700", "bold"}:
            raise ValueError("Unsupported font weight.")
        element_id = self._claim_id(element_id)
        fill = _color(color or self.tokens.foreground)
        lines = str(text).splitlines() or [""]
        spans = "".join(
            f'<tspan x="{x:g}" dy="{0 if i == 0 else font_size_pt*0.48*25.4/72:g}">{escape(line)}</tspan>'
            for i, line in enumerate(lines)
        )
        self._elements.append(
            f'<text id="{element_id}" x="{x:g}" y="{y:g}" text-anchor="{anchor}" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="{font_size_pt * 25.4 / 72:g}" data-font-size-pt="{font_size_pt:g}" '
            f'font-weight="{weight}" fill="{fill}">{spans}</text>'
        )

    def add_line(self, start: tuple[float, float], end: tuple[float, float], *,
                 color: str | None = None, width_pt: float = 1.0,
                 element_id: str | None = None, dashed: bool = False) -> None:
        x1, y1 = (_num(v, "line coordinate") for v in start)
        x2, y2 = (_num(v, "line coordinate") for v in end)
        self._inside(x1, y1); self._inside(x2, y2)
        width_pt = _num(width_pt, "width_pt")
        if width_pt <= 0:
            raise ValueError("Line width must be positive.")
        color = _color(color or self.tokens.foreground)
        eid = f' id="{self._claim_id(element_id)}"' if element_id else ""
        dash = ' stroke-dasharray="2,1.5"' if dashed else ""
        self._elements.append(
            f'<path{eid} d="M {x1:g},{y1:g} L {x2:g},{y2:g}" fill="none" '
            f'stroke="{color}" stroke-width="{width_pt * 25.4 / 72:g}"{dash}/>'
        )

    def add_arrow(self, start: tuple[float, float], end: tuple[float, float], *,
                  label: str = "", color: str | None = None, width_pt: float = 1.1,
                  element_id: str | None = None, dashed: bool = False) -> None:
        x1, y1 = (_num(v, "start coordinate") for v in start)
        x2, y2 = (_num(v, "end coordinate") for v in end)
        self._inside(x1, y1); self._inside(x2, y2)
        width_pt = _num(width_pt, "width_pt")
        if width_pt <= 0:
            raise ValueError("Arrow width must be positive.")
        color = _color(color or self.tokens.foreground)
        eid = f' id="{self._claim_id(element_id)}"' if element_id else ""
        dash = ' stroke-dasharray="2,1.5"' if dashed else ""
        self._elements.append(
            f'<path{eid} d="M {x1:g},{y1:g} L {x2:g},{y2:g}" fill="none" '
            f'stroke="{color}" stroke-width="{width_pt * 25.4 / 72:g}" marker-end="url(#arrowhead)"{dash}/>'
        )
        if label:
            self._arrow_count += 1
            label_id = (element_id or f"arrow-{self._arrow_count}") + "-label"
            self.add_text(label_id, (x1+x2)/2,
                          (y1+y2)/2 - 1.2, label, font_size_pt=6.5,
                          color=color, anchor="middle")

    def add_circle(self, element_id: str, cx: float, cy: float, radius: float, *,
                   fill: str = "#FFFFFF", stroke: str | None = None,
                   stroke_width_pt: float = 0.8, label: str = "") -> None:
        cx, cy, radius = _num(cx, "cx"), _num(cy, "cy"), _num(radius, "radius")
        self._inside(cx, cy)
        stroke_width_pt = _num(stroke_width_pt, "stroke_width_pt")
        if stroke_width_pt <= 0:
            raise ValueError("Circle stroke width must be positive.")
        if radius <= 0 or cx-radius < 0 or cy-radius < 0 or cx+radius > self.width_mm or cy+radius > self.height_mm:
            raise ValueError("Circle must fit inside the canvas.")
        eid = self._claim_id(element_id)
        fill, stroke = _color(fill), _color(stroke or self.tokens.foreground)
        self._elements.append(
            f'<circle id="{eid}" cx="{cx:g}" cy="{cy:g}" r="{radius:g}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width_pt * 25.4 / 72:g}" />'
        )
        if label:
            self.add_text(element_id + "-label", cx, cy + 1.0, label,
                          font_size_pt=9.0, anchor="middle")

    def to_svg(self) -> str:
        desc = f'<desc>{escape(str(self.description))}</desc>' if self.description else ""
        body = "\n".join(self._elements)
        return (
            f'<svg xmlns="{SVG_NS}" width="{self.width_mm:g}mm" '
            f'height="{self.height_mm:g}mm" viewBox="0 0 {self.width_mm:g} {self.height_mm:g}" '
            f'role="img" aria-labelledby="diagram-title">'
            f'<title id="diagram-title">{escape(str(self.title))}</title>{desc}'
            '<defs><marker id="arrowhead" markerWidth="3.2" markerHeight="3.2" '
            'refX="2.8" refY="1.6" orient="auto" markerUnits="strokeWidth">'
            '<path d="M0,0 L3.2,1.6 L0,3.2 z" fill="#20242A"/></marker></defs>'
            f'<rect width="100%" height="100%" fill="{_color(self.tokens.background)}"/>'
            f'{body}</svg>'
        )

    def save_svg(self, path: str | Path) -> Path:
        target = Path(path)
        if target.suffix.lower() != ".svg":
            raise ValueError("save_svg expects an .svg path.")
        target.parent.mkdir(parents=True, exist_ok=True)
        content = self.to_svg()
        ET.fromstring(content)
        target.write_text(content, encoding="utf-8")
        return target
