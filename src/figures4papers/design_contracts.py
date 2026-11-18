"""Validation for structured scientific figure briefs and scene graphs."""
from __future__ import annotations

import math
from typing import Any, Mapping

from .diagram import DiagramCanvas


class DesignContractError(ValueError):
    """A design brief or scene graph violates its versioned contract."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DesignContractError(f"{field} must be a nonblank string.")
    return value.strip()


def _positive(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DesignContractError(f"{field} must be numeric.") from exc
    if not math.isfinite(number) or number <= 0:
        raise DesignContractError(f"{field} must be finite and positive.")
    return number


def validate_design_brief(brief: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the semantic design decision before any geometry is generated."""
    if brief.get("schema_version") != "1.0":
        raise DesignContractError("Unsupported design-brief schema_version.")
    for key in ("brief_id", "research_question", "intended_takeaway", "figure_role"):
        _text(brief.get(key), key)
    blocks = brief.get("content_blocks")
    panels = brief.get("panel_plan")
    if not isinstance(blocks, list) or not blocks:
        raise DesignContractError("content_blocks must be a nonempty list.")
    if not isinstance(panels, list) or not panels:
        raise DesignContractError("panel_plan must be a nonempty list.")
    block_ids = set()
    for block in blocks:
        block_id = _text(block.get("id"), "content_blocks[].id")
        if block_id in block_ids:
            raise DesignContractError(f"Duplicate content block id: {block_id}")
        block_ids.add(block_id)
        _text(block.get("label"), "content_blocks[].label")
        _text(block.get("scientific_role"), "content_blocks[].scientific_role")
    panel_ids = set()
    for panel in panels:
        panel_id = _text(panel.get("panel_id"), "panel_plan[].panel_id")
        if panel_id in panel_ids:
            raise DesignContractError(f"Duplicate panel_id: {panel_id}")
        panel_ids.add(panel_id)
        _text(panel.get("claim"), "panel_plan[].claim")
        _text(panel.get("visual_form"), "panel_plan[].visual_form")
        refs = panel.get("content_block_ids", [])
        if not isinstance(refs, list) or any(ref not in block_ids for ref in refs):
            raise DesignContractError(f"Panel {panel_id} refers to an unknown content block.")
    references = brief.get("references", [])
    if not isinstance(references, list):
        raise DesignContractError("references must be a list.")
    for reference in references:
        _text(reference.get("figure_id"), "references[].figure_id")
        _text(reference.get("reason_for_use"), "references[].reason_for_use")
    constraints = brief.get("constraints", {})
    if not isinstance(constraints, dict):
        raise DesignContractError("constraints must be an object.")
    return dict(brief)


def validate_scene(scene: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a renderer-neutral scene graph in physical millimetres."""
    if scene.get("schema_version") != "1.0":
        raise DesignContractError("Unsupported scene schema_version.")
    _text(scene.get("figure_id"), "figure_id")
    _text(scene.get("title"), "title")
    canvas = scene.get("canvas")
    if not isinstance(canvas, dict) or canvas.get("units") != "mm":
        raise DesignContractError("canvas must declare units='mm'.")
    width = _positive(canvas.get("width_mm"), "canvas.width_mm")
    height = _positive(canvas.get("height_mm"), "canvas.height_mm")
    layout = scene.get("layout")
    if not isinstance(layout, dict) or layout.get("mode") not in {"manual", "layered"}:
        raise DesignContractError("layout.mode must be manual or layered.")
    nodes = scene.get("nodes")
    edges = scene.get("edges", [])
    if not isinstance(nodes, list) or not nodes:
        raise DesignContractError("nodes must be a nonempty list.")
    if not isinstance(edges, list):
        raise DesignContractError("edges must be a list.")
    node_map = {}
    for node in nodes:
        node_id = _text(node.get("id"), "nodes[].id")
        if node_id in node_map:
            raise DesignContractError(f"Duplicate node id: {node_id}")
        if node.get("type") not in {"box", "ellipse"}:
            raise DesignContractError(f"Unsupported node type: {node.get('type')}")
        _text(node.get("label"), f"nodes[{node_id}].label")
        node_width = _positive(node.get("width_mm"), f"nodes[{node_id}].width_mm")
        node_height = _positive(node.get("height_mm"), f"nodes[{node_id}].height_mm")
        if layout["mode"] == "manual":
            x = float(node.get("x_mm", float("nan")))
            y = float(node.get("y_mm", float("nan")))
            if not math.isfinite(x) or not math.isfinite(y):
                raise DesignContractError(f"Manual layout requires x_mm/y_mm for node {node_id}.")
            if x < 0 or y < 0 or x + node_width > width or y + node_height > height:
                raise DesignContractError(f"Node {node_id} falls outside the canvas.")
        node_map[node_id] = node
    edge_ids = set()
    for edge in edges:
        edge_id = _text(edge.get("id"), "edges[].id")
        if edge_id in edge_ids or edge_id in node_map:
            raise DesignContractError(f"Duplicate scene element id: {edge_id}")
        edge_ids.add(edge_id)
        source = _text(edge.get("source"), f"edges[{edge_id}].source")
        target = _text(edge.get("target"), f"edges[{edge_id}].target")
        if source not in node_map or target not in node_map:
            raise DesignContractError(f"Edge {edge_id} refers to an unknown node.")
        if source == target and edge.get("kind") != "self_loop":
            raise DesignContractError(f"Edge {edge_id} is a self-loop but is not declared self_loop.")
    return dict(scene)


def _boundary_point(node: Mapping[str, Any], toward: tuple[float, float]) -> tuple[float, float]:
    x, y = float(node["x_mm"]), float(node["y_mm"])
    width, height = float(node["width_mm"]), float(node["height_mm"])
    cx, cy = x + width / 2, y + height / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    if node["type"] == "ellipse":
        scale = 1.0 / math.sqrt((dx / (width / 2)) ** 2 + (dy / (height / 2)) ** 2)
    else:
        scale = min(
            (width / 2) / abs(dx) if dx else float("inf"),
            (height / 2) / abs(dy) if dy else float("inf"),
        )
    return cx + dx * scale, cy + dy * scale


def render_scene_svg(scene: Mapping[str, Any]) -> str:
    """Render a manually laid-out scene through the existing deterministic SVG engine.

    The v0.3 first slice intentionally supports manual coordinates only. A
    layered/ELK adapter is a separate implementation milestone, not silently
    approximated by this renderer.
    """
    scene = validate_scene(scene)
    if scene["layout"]["mode"] != "manual":
        raise NotImplementedError("Layered layout is specified but not yet implemented in v0.3.")
    canvas_spec = scene["canvas"]
    canvas = DiagramCanvas(
        canvas_spec["width_mm"], canvas_spec["height_mm"],
        title=scene["title"], description=scene.get("description", ""),
    )
    nodes = {node["id"]: node for node in scene["nodes"]}
    styles = {
        "primary": ("#EAF1F7", "#4477AA"),
        "secondary": ("#F2F3F5", "#697586"),
        "accent": ("#EAF5F0", "#26866A"),
        "warning": ("#FFF4E5", "#B7791F"),
    }
    for node in scene["nodes"]:
        fill, stroke = styles.get(node.get("style_token", "primary"), styles["primary"])
        if node["type"] == "box":
            canvas.add_box(
                node["id"], node["x_mm"], node["y_mm"],
                node["width_mm"], node["height_mm"], node["label"],
                subtitle=node.get("subtitle", ""), fill=node.get("fill", fill),
                stroke=node.get("stroke", stroke),
                font_size_pt=float(node.get("font_size_pt", 8.0)),
            )
        else:
            radius = min(float(node["width_mm"]), float(node["height_mm"])) / 2
            canvas.add_circle(
                node["id"], float(node["x_mm"]) + float(node["width_mm"]) / 2,
                float(node["y_mm"]) + float(node["height_mm"]) / 2, radius,
                fill=node.get("fill", fill), stroke=node.get("stroke", stroke),
                label=node["label"],
            )
    for edge in scene.get("edges", []):
        source, target = nodes[edge["source"]], nodes[edge["target"]]
        source_center = (
            float(source["x_mm"]) + float(source["width_mm"]) / 2,
            float(source["y_mm"]) + float(source["height_mm"]) / 2,
        )
        target_center = (
            float(target["x_mm"]) + float(target["width_mm"]) / 2,
            float(target["y_mm"]) + float(target["height_mm"]) / 2,
        )
        start = _boundary_point(source, target_center)
        end = _boundary_point(target, source_center)
        canvas.add_arrow(
            start, end, label=edge.get("label", ""),
            element_id=edge["id"], dashed=edge.get("style") == "dashed",
        )
    return canvas.to_svg()
