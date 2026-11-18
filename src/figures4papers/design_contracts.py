"""Validation for structured scientific figure briefs and scene graphs."""
from __future__ import annotations

import math
import re
from collections import deque
from typing import Any, Mapping

from .diagram import DiagramCanvas
from .schema_validation import SchemaValidationError, validate_json_document

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_STYLE_TOKENS = {"primary", "secondary", "accent", "warning"}
_EDGE_KINDS = {"data_flow", "control_flow", "skip", "attention", "feedback", "self_loop", "other"}
_RELATION_KINDS = _EDGE_KINDS - {"self_loop"}


class DesignContractError(ValueError):
    """A design brief or scene graph violates its versioned contract."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DesignContractError(f"{field} must be a nonblank string.")
    return value.strip()


def _positive(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise DesignContractError(f"{field} must be numeric, not boolean.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DesignContractError(f"{field} must be numeric.") from exc
    if not math.isfinite(number) or number <= 0:
        raise DesignContractError(f"{field} must be finite and positive.")
    return number


def _validate_schema(instance: Mapping[str, Any], schema_name: str) -> None:
    try:
        validate_json_document(instance, schema_name)
    except SchemaValidationError as exc:
        raise DesignContractError(str(exc)) from exc


def _validate_constraints(constraints: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "target_venue", "target_width_mm", "target_height_mm", "preferred_layout",
        "minimum_font_size_pt", "output_formats",
    }
    unknown = set(constraints) - allowed
    if unknown:
        raise DesignContractError(f"Unknown design constraints: {sorted(unknown)}")
    for key in ("target_width_mm", "target_height_mm", "minimum_font_size_pt"):
        if key in constraints:
            _positive(constraints[key], f"constraints.{key}")
    if "preferred_layout" in constraints:
        _text(constraints["preferred_layout"], "constraints.preferred_layout")
    if "output_formats" in constraints:
        formats = constraints["output_formats"]
        allowed_formats = {"svg", "pdf", "png", "drawio", "pptx"}
        if (not isinstance(formats, list) or not formats
                or any(item not in allowed_formats for item in formats)
                or len(set(formats)) != len(formats)):
            raise DesignContractError("constraints.output_formats must contain unique supported formats.")
    return dict(constraints)


def validate_design_brief(brief: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the semantic design decision before any geometry is generated."""
    if not isinstance(brief, Mapping):
        raise DesignContractError("Design Brief must be an object.")
    _validate_schema(brief, "design-brief.schema.json")
    if brief.get("schema_version") != "1.0":
        raise DesignContractError("Unsupported design-brief schema_version.")
    for key in ("brief_id", "research_question", "intended_takeaway", "figure_role"):
        _text(brief.get(key), key)
    blocks, panels = brief.get("content_blocks"), brief.get("panel_plan")
    block_ids = set()
    for block in blocks:
        block_id = _text(block.get("id"), "content_blocks[].id")
        if block_id in block_ids:
            raise DesignContractError(f"Duplicate content block id: {block_id}")
        block_ids.add(block_id)
        for key in ("label", "scientific_role", "description"):
            _text(block.get(key), f"content_blocks[].{key}")
    panel_ids = set()
    assigned_blocks = set()
    for panel in panels:
        panel_id = _text(panel.get("panel_id"), "panel_plan[].panel_id")
        if panel_id in panel_ids:
            raise DesignContractError(f"Duplicate panel_id: {panel_id}")
        panel_ids.add(panel_id)
        _text(panel.get("claim"), "panel_plan[].claim")
        _text(panel.get("visual_form"), "panel_plan[].visual_form")
        refs = panel.get("content_block_ids", [])
        if not refs or len(refs) != len(set(refs)):
            raise DesignContractError(f"Panel {panel_id} must contain unique content_block_ids.")
        if any(ref not in block_ids for ref in refs):
            raise DesignContractError(f"Panel {panel_id} refers to an unknown content block.")
        assigned_blocks.update(refs)
    missing_blocks = block_ids - assigned_blocks
    if missing_blocks:
        raise DesignContractError(
            f"Content blocks are not assigned to any panel: {sorted(missing_blocks)}"
        )
    for reference in brief.get("references", []):
        _text(reference.get("figure_id"), "references[].figure_id")
        _text(reference.get("reason_for_use"), "references[].reason_for_use")
    constraints = brief.get("constraints", {})
    if not isinstance(constraints, Mapping):
        raise DesignContractError("constraints must be an object.")
    _validate_constraints(constraints)
    for relation in brief.get("required_relations", []):
        source_id = _text(relation.get("source_block_id"), "required_relations[].source_block_id")
        target_id = _text(relation.get("target_block_id"), "required_relations[].target_block_id")
        relation_type = _text(relation.get("relation_type"), "required_relations[].relation_type")
        if source_id not in block_ids or target_id not in block_ids:
            raise DesignContractError("Required relations must refer to known content blocks.")
        if source_id == target_id:
            raise DesignContractError("Required relations cannot connect a content block to itself.")
        if relation_type not in _RELATION_KINDS:
            raise DesignContractError(f"Unsupported required relation type: {relation_type}")
        if "must_be_direct" in relation and not isinstance(relation["must_be_direct"], bool):
            raise DesignContractError("required_relations[].must_be_direct must be boolean.")
    return dict(brief)


def validate_scene(scene: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a renderer-neutral scene graph in physical millimetres."""
    if not isinstance(scene, Mapping):
        raise DesignContractError("Scene Graph must be an object.")
    _validate_schema(scene, "scene.schema.json")
    if scene.get("schema_version") != "1.0":
        raise DesignContractError("Unsupported scene schema_version.")
    _text(scene.get("figure_id"), "figure_id")
    _text(scene.get("title"), "title")
    canvas = scene.get("canvas")
    if not isinstance(canvas, Mapping) or canvas.get("units") != "mm":
        raise DesignContractError("canvas must declare units='mm'.")
    width = _positive(canvas.get("width_mm"), "canvas.width_mm")
    height = _positive(canvas.get("height_mm"), "canvas.height_mm")
    layout = scene.get("layout")
    if not isinstance(layout, Mapping) or layout.get("mode") not in {"manual", "layered"}:
        raise DesignContractError("layout.mode must be manual or layered.")
    engine = layout.get("engine")
    if engine is not None and engine not in {"manual", "elk-layered"}:
        raise DesignContractError("layout.engine must be manual or elk-layered.")
    if layout["mode"] == "manual" and engine not in {None, "manual"}:
        raise DesignContractError("Manual layout must use the manual engine.")
    if layout["mode"] == "layered" and engine not in {None, "elk-layered"}:
        raise DesignContractError("Layered layout must use the elk-layered engine.")
    if "direction" in layout and layout["direction"] not in {"LR", "TB"}:
        raise DesignContractError("layout.direction must be LR or TB.")
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
        if "font_size_pt" in node:
            _positive(node["font_size_pt"], f"nodes[{node_id}].font_size_pt")
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
        kind = edge.get("kind", "other")
        if kind not in _EDGE_KINDS:
            raise DesignContractError(f"Unsupported edge kind on {edge_id}: {kind}")
        if source == target and kind != "self_loop":
            raise DesignContractError(f"Edge {edge_id} is a self-loop but is not declared self_loop.")
        if source != target and kind == "self_loop":
            raise DesignContractError(f"Edge {edge_id} declares self_loop but has distinct endpoints.")
        if edge.get("style", "solid") not in {"solid", "dashed"}:
            raise DesignContractError(f"Unsupported edge style on {edge_id}.")
        if edge.get("route", "straight") not in {"straight", "orthogonal", "spline"}:
            raise DesignContractError(f"Unsupported edge route on {edge_id}.")
        if "font_size_pt" in edge:
            _positive(edge["font_size_pt"], f"edges[{edge_id}].font_size_pt")
    return dict(scene)


def validate_scene_constraints(brief: Mapping[str, Any], scene: Mapping[str, Any]) -> dict[str, Any]:
    """Enforce physical and typographic constraints from a Design Brief."""
    constraints = brief.get("constraints", {})
    canvas = scene["canvas"]
    for key, actual_key in (("target_width_mm", "width_mm"), ("target_height_mm", "height_mm")):
        if key in constraints and not math.isclose(
            float(constraints[key]), float(canvas[actual_key]), rel_tol=0, abs_tol=1e-6
        ):
            raise DesignContractError(
                f"Scene canvas {actual_key}={canvas[actual_key]} violates {key}={constraints[key]}."
            )
    minimum_font = float(constraints.get("minimum_font_size_pt", 0))
    if minimum_font:
        for edge in scene.get("edges", []):
            if edge.get("label") and float(edge.get("font_size_pt", 7.0)) < minimum_font:
                raise DesignContractError(
                    f"Edge {edge['id']} uses a label below minimum_font_size_pt={minimum_font}."
                )
        for node in scene["nodes"]:
            base_size = float(node.get("font_size_pt", 8.0))
            rendered_sizes = [base_size]
            if node.get("subtitle"):
                rendered_sizes.append(max(6.0, base_size - 1.0))
            if min(rendered_sizes) < minimum_font:
                raise DesignContractError(
                    f"Node {node['id']} uses text below minimum_font_size_pt={minimum_font}."
                )
    preferred = constraints.get("preferred_layout")
    if preferred == "left_to_right" and scene["layout"].get("direction") != "LR":
        raise DesignContractError("Design Brief requires left_to_right layout (direction='LR').")
    if preferred == "top_to_bottom" and scene["layout"].get("direction") != "TB":
        raise DesignContractError("Design Brief requires top_to_bottom layout (direction='TB').")
    if preferred and preferred not in {"left_to_right", "top_to_bottom"}:
        if scene["layout"].get("pattern") != preferred:
            raise DesignContractError(f"Scene layout pattern does not satisfy preferred_layout={preferred}.")
    return {"minimum_font_size_pt": minimum_font or None, "preferred_layout": preferred}


def validate_scene_against_brief(
    brief: Mapping[str, Any],
    scene: Mapping[str, Any],
    *,
    atlas: Any | None = None,
) -> dict[str, Any]:
    """Enforce traceability from planned scientific content to rendered nodes."""
    brief = validate_design_brief(brief)
    scene = validate_scene(scene)
    if scene.get("brief_id") != brief["brief_id"]:
        raise DesignContractError("Scene must carry a brief_id matching the supplied Design Brief.")
    blocks = {block["id"]: block for block in brief["content_blocks"]}
    panels = {panel["panel_id"]: panel for panel in brief["panel_plan"]}
    mapped: dict[str, set[str]] = {panel_id: set() for panel_id in panels}
    for node in scene["nodes"]:
        block_id, panel_id = node.get("content_block_id"), node.get("panel_id")
        role = node.get("scientific_role")
        if block_id:
            if block_id not in blocks:
                raise DesignContractError(f"Node {node['id']} refers to unknown content block {block_id}.")
            if not role:
                raise DesignContractError(f"Scientific node {node['id']} must declare scientific_role.")
            expected_role = blocks[block_id]["scientific_role"]
            if role != expected_role:
                raise DesignContractError(f"Node {node['id']} scientific_role conflicts with content block {block_id}.")
            if panel_id is None and len(panels) == 1:
                panel_id = next(iter(panels))
            if panel_id not in panels:
                raise DesignContractError(f"Scientific node {node['id']} must map to a known panel_id.")
            if block_id not in panels[panel_id]["content_block_ids"]:
                raise DesignContractError(
                    f"Node {node['id']} maps content block {block_id} to a panel that does not declare it."
                )
            mapped[panel_id].add(block_id)
        elif role != "decorative":
            raise DesignContractError(
                f"Node {node['id']} must map to a content_block_id or declare scientific_role='decorative'."
            )
        elif panel_id is not None and panel_id not in panels:
            raise DesignContractError(f"Decorative node {node['id']} refers to unknown panel {panel_id}.")
    for panel_id, panel in panels.items():
        missing = set(panel["content_block_ids"]) - mapped[panel_id]
        if missing:
            raise DesignContractError(f"Panel {panel_id} is missing scene nodes for content blocks: {sorted(missing)}")
    if atlas is not None:
        known_figure_ids = set(atlas.figures)
        unknown_references = [
            item["figure_id"] for item in brief.get("references", [])
            if item["figure_id"] not in known_figure_ids
        ]
        if unknown_references:
            raise DesignContractError(f"Design Brief references unknown Atlas figure IDs: {unknown_references}")
    nodes_by_id = {node["id"]: node for node in scene["nodes"]}
    adjacency: dict[str, list[tuple[str, str]]] = {}
    direct_relations = set()
    for edge in scene.get("edges", []):
        source_block = nodes_by_id[edge["source"]].get("content_block_id")
        target_block = nodes_by_id[edge["target"]].get("content_block_id")
        if source_block and target_block:
            kind = edge.get("kind", "other")
            direct_relations.add((source_block, target_block, kind))
            adjacency.setdefault(source_block, []).append((target_block, kind))
    for relation in brief.get("required_relations", []):
        source_id = relation["source_block_id"]
        target_id = relation["target_block_id"]
        relation_type = relation["relation_type"]
        if relation.get("must_be_direct", True):
            matched = (source_id, target_id, relation_type) in direct_relations
        else:
            queue = deque([source_id])
            visited = {source_id}
            while queue and target_id not in visited:
                current = queue.popleft()
                for neighbor, edge_kind in adjacency.get(current, []):
                    if edge_kind == relation_type and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            matched = target_id in visited
        if not matched:
            raise DesignContractError(
                f"Scene Graph does not preserve typed relation: {source_id} -[{relation_type}]-> {target_id}."
            )
    validate_scene_constraints(brief, scene)
    return dict(scene)


def validate_renderer_capabilities(scene: Mapping[str, Any], renderer: str) -> dict[str, Any]:
    """Reject valid Scene Graph features that a specific renderer cannot preserve."""
    scene = validate_scene(scene)
    if renderer not in {"svg", "drawio"}:
        raise DesignContractError(f"Unknown renderer: {renderer}")
    if scene["layout"]["mode"] != "manual":
        raise NotImplementedError(f"{renderer} renderer currently requires manual layout.")
    for edge in scene.get("edges", []):
        route = edge.get("route", "straight")
        if route == "spline":
            raise NotImplementedError(f"{renderer} renderer does not support spline routing.")
        if edge.get("kind") == "self_loop" or edge["source"] == edge["target"]:
            raise NotImplementedError(f"{renderer} renderer does not yet support self-loop geometry.")
    if renderer == "svg":
        for node in scene["nodes"]:
            if node["type"] == "ellipse" and not math.isclose(
                float(node["width_mm"]), float(node["height_mm"]), rel_tol=0, abs_tol=1e-9
            ):
                raise NotImplementedError("SVG renderer currently supports circular, not elliptical, scene nodes.")
    return {"renderer": renderer, "supported": True}


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
    validate_renderer_capabilities(scene, "svg")
    canvas_spec = scene["canvas"]
    canvas = DiagramCanvas(canvas_spec["width_mm"], canvas_spec["height_mm"],
                           title=scene["title"], description=scene.get("description", ""))
    nodes = {node["id"]: node for node in scene["nodes"]}
    styles = {"primary": ("#EAF1F7", "#4477AA"), "secondary": ("#F2F3F5", "#697586"),
              "accent": ("#EAF5F0", "#26866A"), "warning": ("#FFF4E5", "#B7791F")}
    for node in scene["nodes"]:
        fill, stroke = styles.get(node.get("style_token", "primary"), styles["primary"])
        font_size = float(node.get("font_size_pt", 8.0))
        if node["type"] == "box":
            canvas.add_box(node["id"], node["x_mm"], node["y_mm"], node["width_mm"], node["height_mm"],
                           node["label"], subtitle=node.get("subtitle", ""), fill=node.get("fill", fill),
                           stroke=node.get("stroke", stroke), font_size_pt=font_size)
        else:
            radius = float(node["width_mm"]) / 2
            canvas.add_circle(node["id"], float(node["x_mm"]) + radius, float(node["y_mm"]) + radius,
                              radius, fill=node.get("fill", fill), stroke=node.get("stroke", stroke),
                              label=node["label"], font_size_pt=font_size)
    for edge in scene.get("edges", []):
        source, target = nodes[edge["source"]], nodes[edge["target"]]
        source_center = (float(source["x_mm"]) + float(source["width_mm"]) / 2,
                         float(source["y_mm"]) + float(source["height_mm"]) / 2)
        target_center = (float(target["x_mm"]) + float(target["width_mm"]) / 2,
                         float(target["y_mm"]) + float(target["height_mm"]) / 2)
        start = _boundary_point(source, target_center)
        end = _boundary_point(target, source_center)
        kwargs = {
            "label": edge.get("label", ""),
            "element_id": edge["id"],
            "dashed": edge.get("style") == "dashed",
            "label_font_size_pt": float(edge.get("font_size_pt", 7.0)),
        }
        if edge.get("route", "straight") == "straight":
            canvas.add_arrow(start, end, **kwargs)
        else:
            mid_x = (start[0] + end[0]) / 2
            canvas.add_routed_arrow(
                [start, (mid_x, start[1]), (mid_x, end[1]), end],
                **kwargs,
            )
    return canvas.to_svg()
