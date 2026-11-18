"""Editable draw.io XML export for the v0.3 manual scene-graph subset."""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Any, Mapping

from .design_contracts import validate_scene

MM_TO_PX = 96.0 / 25.4
STYLE = {
    "primary": ("#EAF1F7", "#4477AA"),
    "secondary": ("#F2F3F5", "#697586"),
    "accent": ("#EAF5F0", "#26866A"),
    "warning": ("#FFF4E5", "#B7791F"),
}


def scene_to_drawio_xml(scene: Mapping[str, Any]) -> str:
    """Convert semantic nodes and edges to native mxCell vertices/connectors."""
    scene = validate_scene(scene)
    if scene["layout"]["mode"] != "manual":
        raise NotImplementedError("draw.io export currently requires manual scene coordinates.")
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
    for node in scene["nodes"]:
        fill, stroke = STYLE.get(node.get("style_token", "primary"), STYLE["primary"])
        fill = node.get("fill", fill)
        stroke = node.get("stroke", stroke)
        shape = "ellipse" if node["type"] == "ellipse" else "rounded=1"
        style = (
            f"{shape};whiteSpace=wrap;html=0;fillColor={fill};strokeColor={stroke};"
            f"fontSize={round(float(node.get('font_size_pt', 8.0)))};"
            "fontFamily=Arial;align=center;verticalAlign=middle;"
        )
        cell = ET.SubElement(root, "mxCell", {
            "id": node["id"], "value": node["label"], "style": style,
            "vertex": "1", "parent": "1",
        })
        ET.SubElement(cell, "mxGeometry", {
            "x": f"{float(node['x_mm']) * MM_TO_PX:.3f}",
            "y": f"{float(node['y_mm']) * MM_TO_PX:.3f}",
            "width": f"{float(node['width_mm']) * MM_TO_PX:.3f}",
            "height": f"{float(node['height_mm']) * MM_TO_PX:.3f}",
            "as": "geometry",
        })
    for edge in scene.get("edges", []):
        dashed = "dashed=1;" if edge.get("style") == "dashed" else ""
        style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;"
            "jettySize=auto;html=0;endArrow=block;endFill=1;"
            f"{dashed}strokeColor=#344054;"
        )
        cell = ET.SubElement(root, "mxCell", {
            "id": edge["id"], "value": edge.get("label", ""), "style": style,
            "edge": "1", "parent": "1",
            "source": edge["source"], "target": edge["target"],
        })
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    rendered = ET.tostring(mxfile, encoding="unicode", xml_declaration=False)
    # Parse the result again and verify all IDs and endpoint references.
    parsed = ET.fromstring(rendered)
    cells = parsed.findall(".//mxCell")
    ids = [cell.attrib.get("id") for cell in cells]
    if len(ids) != len(set(ids)):
        raise ValueError("Generated draw.io XML contains duplicate cell IDs.")
    known = set(ids)
    for cell in cells:
        for endpoint in ("source", "target"):
            if endpoint in cell.attrib and cell.attrib[endpoint] not in known:
                raise ValueError(f"draw.io edge has unknown {endpoint} reference.")
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
