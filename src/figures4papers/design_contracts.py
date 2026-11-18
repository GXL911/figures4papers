"""Validation for structured scientific figure briefs and scene graphs."""
from __future__ import annotations
import math
import re
from typing import Any, Mapping
from .diagram import DiagramCanvas

class DesignContractError(ValueError):
    """A design brief or scene graph violates its versioned contract."""

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_STYLE_TOKENS = {"primary", "secondary", "accent", "warning"}

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
    blocks, panels = brief.get("content_blocks"), brief.get("panel_plan")
    if not isinstance(blocks, list) or not blocks:
        raise DesignContractError("content_blocks must be a nonempty list.")
    if not isinstance(panels, list) or not panels:
        raise DesignContractError("panel_plan must be a nonempty list.")
    block_ids = set()
    for block in blocks:
        if not isinstance(block, Mapping):
            raise DesignContractError("Each content block must be an object.")
        block_id = _text(block.get("id"), "content_blocks[].id")
        if block_id in block_ids:
            raise DesignContractError(f"Duplicate content block id: {block_id}")
        block_ids.add(block_id)
        for key in ("label", "scientific_role", "description"):
            _text(block.get(key), f"content_blocks[].{key}")
    panel_ids = set()
    for panel in panels:
        if not isinstance(panel, Mapping):
            raise DesignContractError("Each panel plan must be an object.")
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
        if not isinstance(reference, Mapping):
            raise DesignContractError("Each reference must be an object.")
        _text(reference.get("figure_id"), "references[].figure_id")
        _text(reference.get("reason_for_use"), "references[].reason_for_use")
    if not isinstance(brief.get("constraints", {}), dict):
        raise DesignContractError("constraints must be an object.")
    relations = brief.get("required_relations", [])
    if not isinstance(relations, list):
        raise DesignContractError("required_relations must be a list.")
    for relation in relations:
        if not isinstance(relation, Mapping):
            raise DesignContractError("Each required relation must be an object.")
        source_id = _text(relation.get("source_block_id"), "required_relations[].source_block_id")
        target_id = _text(relation.get("target_block_id"), "required_relations[].target_block_id")
        relation_type = _text(relation.get("relation_type"), "required_relations[].relation_type")
        if source_id not in block_ids or target_id not in block_ids:
            raise DesignContractError("Required relations must refer to known content blocks.")
        if source_id == target_id:
            raise DesignContractError("Required relations cannot connect a content block to itself.")
        if relation_type not in {"data_flow", "control_flow", "skip", "attention", "feedback", "other"}:
            raise DesignContractError(f"Unsupported required relation type: {relation_type}")
        if "must_be_direct" in relation and not isinstance(relation["must_be_direct"], bool):
            raise DesignContractError("required_relations[].must_be_direct must be boolean.")
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
    nodes, edges = scene.get("nodes"), scene.get("edges", [])
    if not isinstance(nodes, list) or not nodes:
        raise DesignContractError("nodes must be a nonempty list.")
    if not isinstance(edges, list):
        raise DesignContractError("edges must be a list.")
    node_map = {}
    for node in nodes:
        if not isinstance(node, Mapping):
            raise DesignContractError("Each scene node must be an object.")
        node_id = _text(node.get("id"), "nodes[].id")
        if node_id in {"0", "1"}:
            raise DesignContractError("Scene node IDs '0' and '1' are reserved by draw.io.")
        if node_id in node_map:
            raise DesignContractError(f"Duplicate node id: {node_id}")
        if node.get("type") not in {"box", "ellipse"}:
            raise DesignContractError(f"Unsupported node type: {node.get('type')}")
        _text(node.get("label"), f"nodes[{node_id}].label")
        node_width = _positive(node.get("width_mm"), f"nodes[{node_id}].width_mm")
        node_height = _positive(node.get("height_mm"), f"nodes[{node_id}].height_mm")
        if node.get("style_token", "primary") not in _STYLE_TOKENS:
            raise DesignContractError(f"Unknown style_token on node {node_id}.")
        for semantic_key in ("content_block_id", "scientific_role", "panel_id", "evidence_source"):
            if semantic_key in node:
                _text(node[semantic_key], f"nodes[{node_id}].{semantic_key}")
        for color_key in ("fill", "stroke"):
            if color_key in node and not _HEX_COLOR.fullmatch(str(node[color_key])):
                raise DesignContractError(f"nodes[{node_id}].{color_key} must be a six-digit hex color.")
        if layout["mode"] == "manual":
            try:
                x, y = float(node["x_mm"]), float(node["y_mm"])
            except (KeyError, TypeError, ValueError) as exc:
                raise DesignContractError(f"Manual layout requires x_mm/y_mm for node {node_id}.") from exc
            if not math.isfinite(x) or not math.isfinite(y):
                raise DesignContractError(f"Node {node_id} coordinates must be finite.")
            if x < 0 or y < 0 or x + node_width > width or y + node_height > height:
                raise DesignContractError(f"Node {node_id} falls outside the canvas.")
        node_map[node_id] = node
    edge_ids = set()
    for edge in edges:
        if not isinstance(edge, Mapping):
            raise DesignContractError("Each scene edge must be an object.")
        edge_id = _text(edge.get("id"), "edges[].id")
        if edge_id in {"0", "1"} or edge_id in edge_ids or edge_id in node_map:
            raise DesignContractError(f"Duplicate or reserved scene element id: {edge_id}")
        edge_ids.add(edge_id)
        source = _text(edge.get("source"), f"edges[{edge_id}].source")
        target = _text(edge.get("target"), f"edges[{edge_id}].target")
        if source not in node_map or target not in node_map:
            raise DesignContractError(f"Edge {edge_id} refers to an unknown node.")
        if source == target and edge.get("kind") != "self_loop":
            raise DesignContractError(f"Edge {edge_id} is a self-loop but is not declared self_loop.")
        if edge.get("style", "solid") not in {"solid", "dashed"}:
            raise DesignContractError(f"Unsupported edge style on {edge_id}.")
        if edge.get("route", "straight") not in {"straight", "orthogonal", "spline"}:
            raise DesignContractError(f"Unsupported edge route on {edge_id}.")
    return dict(scene)

def validate_scene_against_brief(brief: Mapping[str, Any], scene: Mapping[str, Any]) -> dict[str, Any]:
    """Enforce traceability from planned scientific content to rendered nodes."""
    brief = validate_design_brief(brief)
    scene = validate_scene(scene)
    if scene.get("brief_id") and scene["brief_id"] != brief["brief_id"]:
        raise DesignContractError("Scene brief_id does not match the supplied Design Brief.")
    blocks = {block["id"]: block for block in brief["content_blocks"]}
    panels = {panel["panel_id"]: panel for panel in brief["panel_plan"]}
    mapped: dict[str, set[str]] = {panel_id: set() for panel_id in panels}
    for node in scene["nodes"]:
        block_id, panel_id = node.get("content_block_id"), node.get("panel_id")
        if block_id and block_id not in blocks:
            raise DesignContractError(f"Node {node['id']} refers to unknown content block {block_id}.")
        if panel_id and panel_id not in panels:
            raise DesignContractError(f"Node {node['id']} refers to unknown panel {panel_id}.")
        if block_id:
            expected_role = blocks[block_id]["scientific_role"]
            if node.get("scientific_role") and node["scientific_role"] != expected_role:
                raise DesignContractError(f"Node {node['id']} scientific_role conflicts with content block {block_id}.")
            if panel_id:
                mapped[panel_id].add(block_id)
            elif len(panels) == 1:
                mapped[next(iter(panels))].add(block_id)
            else:
                raise DesignContractError(f"Node {node['id']} needs panel_id because the brief has multiple panels.")
    for panel_id, panel in panels.items():
        missing = set(panel.get("content_block_ids", [])) - mapped[panel_id]
        if missing:
            raise DesignContractError(f"Panel {panel_id} is missing scene nodes for content blocks: {sorted(missing)}")
    nodes_by_id = {node["id"]: node for node in scene["nodes"]}
    block_nodes: dict[str, set[str]] = {}
    for node in scene["nodes"]:
        if node.get("content_block_id"):
            block_nodes.setdefault(node["content_block_id"], set()).add(node["id"])
    direct_relations = set()
    adjacency: dict[str, set[str]] = {}
    for edge in scene.get("edges", []):
        source_block = nodes_by_id[edge["source"]].get("content_block_id")
        target_block = nodes_by_id[edge["target"]].get("content_block_id")
        if source_block and target_block:
            direct_relations.add((source_block, target_block, edge.get("kind", "other")))
            adjacency.setdefault(source_block, set()).add(target_block)
    for relation in brief.get("required_relations", []):
        source_id = relation["source_block_id"]
        target_id = relation["target_block_id"]
        relation_type = relation["relation_type"]
        if relation.get("must_be_direct", True):
            matched = (source_id, target_id, relation_type) in direct_relations
        else:
            frontier, visited = [source_id], {source_id}
            while frontier and target_id not in visited:
                current = frontier.pop(0)
                for neighbor in adjacency.get(current, set()) - visited:
                    visited.add(neighbor)
                    frontier.append(neighbor)
            matched = target_id in visited
        if not matched:
            raise DesignContractError(
                f"Scene Graph does not preserve required relation: {source_id} -[{relation_type}]-> {target_id}."
            )
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
        scale = min((width / 2) / abs(dx) if dx else float("inf"),
                    (height / 2) / abs(dy) if dy else float("inf"))
    return cx + dx * scale, cy + dy * scale

def render_scene_svg(scene: Mapping[str, Any]) -> str:
    """Render a manually laid-out scene through the existing deterministic SVG engine."""
    scene = validate_scene(scene)
    if scene["layout"]["mode"] != "manual":
        raise NotImplementedError("Layered layout is specified but not yet implemented in v0.3.")
    canvas_spec = scene["canvas"]
    canvas = DiagramCanvas(canvas_spec["width_mm"], canvas_spec["height_mm"],
                           title=scene["title"], description=scene.get("description", ""))
    nodes = {node["id"]: node for node in scene["nodes"]}
    styles = {"primary": ("#EAF1F7", "#4477AA"), "secondary": ("#F2F3F5", "#697586"),
              "accent": ("#EAF5F0", "#26866A"), "warning": ("#FFF4E5", "#B7791F")}
    for node in scene["nodes"]:
        fill, stroke = styles.get(node.get("style_token", "primary"), styles["primary"])
        if node["type"] == "box":
            canvas.add_box(node["id"], node["x_mm"], node["y_mm"], node["width_mm"], node["height_mm"],
                           node["label"], subtitle=node.get("subtitle", ""), fill=node.get("fill", fill),
                           stroke=node.get("stroke", stroke), font_size_pt=float(node.get("font_size_pt", 8.0)))
        else:
            if not math.isclose(float(node["width_mm"]), float(node["height_mm"]), rel_tol=0, abs_tol=1e-9):
                raise NotImplementedError("SVG renderer currently supports circular, not elliptical, scene nodes.")
            radius = float(node["width_mm"]) / 2
            canvas.add_circle(node["id"], float(node["x_mm"]) + radius, float(node["y_mm"]) + radius,
                              radius, fill=node.get("fill", fill), stroke=node.get("stroke", stroke),
                              label=node["label"])
    for edge in scene.get("edges", []):
        if edge.get("route", "straight") != "straight":
            raise NotImplementedError("SVG renderer currently supports straight connectors only.")
        source, target = nodes[edge["source"]], nodes[edge["target"]]
        source_center = (float(source["x_mm"]) + float(source["width_mm"]) / 2,
                         float(source["y_mm"]) + float(source["height_mm"]) / 2)
        target_center = (float(target["x_mm"]) + float(target["width_mm"]) / 2,
                         float(target["y_mm"]) + float(target["height_mm"]) / 2)
        canvas.add_arrow(_boundary_point(source, target_center), _boundary_point(target, source_center),
                         label=edge.get("label", ""), element_id=edge["id"],
                         dashed=edge.get("style") == "dashed")
    return canvas.to_svg()
