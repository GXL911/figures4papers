"""Editable draw.io XML export for the supported Scene Graph subset."""
from __future__ import annotations

from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Any, Mapping

from .design_contracts import validate_renderer_capabilities, validate_scene

MM_TO_PX = 96.0 / 25.4
PT_TO_PX = 96.0 / 72.0
STYLE = {
    "primary": ("#EAF1F7", "#4477AA"),
    "secondary": ("#F2F3F5", "#697586"),
    "accent": ("#EAF5F0", "#26866A"),
    "warning": ("#FFF4E5", "#B7791F"),
}


def _node_label(node: Mapping[str, Any]) -> str:
    label = escape(str(node["label"]))
    subtitle = str(node.get("subtitle", "")).strip()
    if not subtitle:
        return label
    base_pt = float(node.get("font_size_pt", 8.0))
    subtitle_px = max(6.0, base_pt - 1.0) * PT_TO_PX
    return (
        '<div style="text-align:center;"><b>' + label + "</b></div>"
        '<div style="text-align:center;font-size:' + f"{subtitle_px:.2f}px" + ';">'
        + escape(subtitle) + "</div>"
    )


def scene_to_drawio_xml(scene: Mapping[str, Any]) -> str:
    """Convert semantic nodes and edges to native editable mxCell objects."""
    scene = validate_scene(scene)
    validate_renderer_capabilities(scene, "drawio")
    canvas = scene["canvas"]
    width_px = round(float(canvas["width_mm"]) * MM_TO_PX)
    height_px = round(float(canvas["height_mm"]) * MM_TO_PX)
    mxfile = ET.Element("mxfile", {
        "host": "app.diagrams.net", "type": "device", "version": "24.7.17",
    })
    diagram = ET.SubElement(mxfile, "diagram", {"id": "page-1", "name": "Page-1"})
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": str(width_px), "dy": str(height_px), "grid": "1", "gridSize": "10",
        "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1",
        "fold": "1", "page": "1", "pageScale": "1",
        "pageWidth": str(width_px), "pageHeight": str(height_px),
        "math": "0", "shadow": "0",
    })
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    object_ids = []
    for node in scene["nodes"]:
        fill, stroke = STYLE.get(node.get("style_token", "primary"), STYLE["primary"])
        fill = node.get("fill", fill)
        stroke = node.get("stroke", stroke)
        font_size_px = float(node.get("font_size_pt", 8.0)) * PT_TO_PX
        shape = "ellipse" if node["type"] == "ellipse" else "rounded=1"
        style = (
            f"{shape};whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
            f"fontSize={font_size_px:.2f};fontFamily=Arial;align=center;verticalAlign=middle;"
        )
        attributes = {
            "id": node["id"],
            "label": _node_label(node),
        }
        for key in ("content_block_id", "scientific_role", "panel_id", "evidence_source"):
            if key in node:
                attributes[key] = str(node[key])
        obj = ET.SubElement(root, "object", attributes)
        object_ids.append(node["id"])
        cell = ET.SubElement(obj, "mxCell", {
            "style": style, "vertex": "1", "parent": "1",
        })
        ET.SubElement(cell, "mxGeometry", {
            "x": f"{float(node['x_mm']) * MM_TO_PX:.3f}",
            "y": f"{float(node['y_mm']) * MM_TO_PX:.3f}",
            "width": f"{float(node['width_mm']) * MM_TO_PX:.3f}",
            "height": f"{float(node['height_mm']) * MM_TO_PX:.3f}",
            "as": "geometry",
        })
    for edge in scene.get("edges", []):
        route = edge.get("route", "straight")
        route_style = "edgeStyle=none;" if route == "straight" else (
            "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;"
        )
        dashed = "dashed=1;" if edge.get("style") == "dashed" else ""
        style = (
            route_style + "html=1;endArrow=block;endFill=1;"
            + f"fontFamily=Arial;fontSize={float(edge.get('font_size_pt', 7.0)) * PT_TO_PX:.2f};strokeWidth=1.47;"
            + dashed + "strokeColor=#344054;"
        )
        attributes = {
            "id": edge["id"],
            "label": str(edge.get("label", "")),
            "relation_kind": str(edge.get("kind", "other")),
            "route": route,
        }
        obj = ET.SubElement(root, "object", attributes)
        object_ids.append(edge["id"])
        cell = ET.SubElement(obj, "mxCell", {
            "style": style, "edge": "1", "parent": "1",
            "source": edge["source"], "target": edge["target"],
        })
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    rendered = ET.tostring(mxfile, encoding="unicode", xml_declaration=False)
    parsed = ET.fromstring(rendered)
    ids = ["0", "1", *object_ids]
    if len(ids) != len(set(ids)):
        raise ValueError("Generated draw.io XML contains duplicate cell IDs.")
    known = set(ids)
    for cell in parsed.findall(".//mxCell"):
        for endpoint in ("source", "target"):
            if endpoint in cell.attrib and cell.attrib[endpoint] not in known:
                raise ValueError(f"draw.io edge has unknown {endpoint} reference.")
    if len(parsed.findall(".//mxCell[@vertex='1']")) != len(scene["nodes"]):
        raise ValueError("draw.io export did not preserve every scene node.")
    if len(parsed.findall(".//mxCell[@edge='1']")) != len(scene.get("edges", [])):
        raise ValueError("draw.io export did not preserve every scene edge.")
    return rendered


def export_drawio(scene: Mapping[str, Any], out_path: str | Path) -> Path:
    target = Path(out_path)
    if target.suffix.lower() != ".drawio":
        target = target.with_suffix(".drawio")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(scene_to_drawio_xml(scene), encoding="utf-8")
    if target.stat().st_size < 100:
        raise RuntimeError("draw.io export is unexpectedly small.")
    return target
