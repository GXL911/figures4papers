"""Conservative SVG and palette diagnostics; not a substitute for visual review."""
from __future__ import annotations
import math
import re
import xml.etree.ElementTree as ET

from matplotlib.colors import is_color_like, to_rgba


def _luminance(color: str) -> float:
    rgba = to_rgba(color)
    if rgba[3] < 1.0:
        raise ValueError("Contrast checks require opaque colors; composite alpha first.")
    rgb = rgba[:3]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126*linear[0] + 0.7152*linear[1] + 0.0722*linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG contrast ratio for two opaque sRGB colors."""
    if not is_color_like(foreground) or not is_color_like(background):
        raise ValueError("Both colors must be valid Matplotlib colors.")
    a, b = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def audit_palette(colors: dict[str, str], *, background: str = "#FFFFFF",
                  text_threshold: float = 4.5, grayscale_delta: float = 0.08) -> dict:
    """Report text contrast and pairs that become similar in grayscale.

    Grayscale similarity is a warning only: line styles, markers and labels can
    provide redundant encodings. This function does not claim full WCAG or
    color-vision-deficiency certification.
    """
    if not is_color_like(background):
        raise ValueError("background must be a valid color.")
    if (not math.isfinite(text_threshold) or not math.isfinite(grayscale_delta)
            or text_threshold <= 0 or grayscale_delta < 0):
        raise ValueError("Contrast threshold must be positive and grayscale_delta nonnegative.")
    contrast = {name: contrast_ratio(color, background) for name, color in colors.items()}
    luminance = {name: _luminance(color) for name, color in colors.items()}
    names = list(colors)
    similar = []
    for i, left in enumerate(names):
        for right in names[i+1:]:
            if abs(luminance[left] - luminance[right]) < grayscale_delta:
                similar.append([left, right])
    return {
        "contrast_ratio": contrast,
        "low_text_contrast": [name for name, value in contrast.items() if value < text_threshold],
        "grayscale_similar_pairs": similar,
        "limitations": "Contrast is computed against one opaque background; grayscale similarity is a screening heuristic, not a print proof.",
    }


def audit_svg(svg: str, *, min_font_pt: float = 6.0) -> dict:
    """Check SVG structure, accessibility metadata and declared text sizes."""
    if not math.isfinite(min_font_pt) or min_font_pt <= 0:
        raise ValueError("min_font_pt must be positive.")
    root = ET.fromstring(svg)
    if not root.tag.endswith("svg"):
        raise ValueError("Expected an SVG root element.")
    ids, duplicates, text_sizes = set(), [], []
    text_count = 0
    for element in root.iter():
        element_id = element.attrib.get("id")
        if element_id:
            if element_id in ids:
                duplicates.append(element_id)
            ids.add(element_id)
        if element.tag.endswith("text") or element.tag.endswith("tspan"):
            text_count += 1
            declared_pt = element.attrib.get("data-font-size-pt")
            size = element.attrib.get("font-size")
            style = element.attrib.get("style", "")
            if declared_pt:
                text_sizes.append(float(declared_pt))
            else:
                if not size:
                    match_style = re.search(r"(?:font-size|font)\s*:\s*([0-9.]+)\s*(pt|px|mm)?", style)
                    if match_style:
                        size = match_style.group(1) + (match_style.group(2) or "px")
                if size:
                    match = re.fullmatch(r"\s*([0-9.]+)\s*(pt|px|mm)?\s*", size)
                    if match:
                        value = float(match.group(1))
                        unit = match.group(2) or "px"
                        if unit == "mm":
                            text_sizes.append(value * 72 / 25.4)
                        elif unit == "px" or unit is None:
                            text_sizes.append(value * 72 / 96)
                        else:
                            text_sizes.append(value)
    has_title = any(element.tag.endswith("title") and (element.text or "").strip() for element in root.iter())
    has_viewbox = bool(root.attrib.get("viewBox"))
    issues = []
    if not has_title:
        issues.append("missing_title")
    if not root.attrib.get("role"):
        issues.append("missing_role")
    if not has_viewbox:
        issues.append("missing_viewBox")
    if duplicates:
        issues.append("duplicate_ids")
    if any(size < min_font_pt for size in text_sizes):
        issues.append("small_text")
    return {
        "has_title": has_title, "has_role": bool(root.attrib.get("role")),
        "has_viewBox": has_viewbox, "text_elements": text_count,
        "minimum_declared_font_pt": min(text_sizes) if text_sizes else None,
        "duplicate_ids": duplicates,
        "small_text_count": sum(size < min_font_pt for size in text_sizes),
        "issues": issues,
        "limitations": "Sizes are estimated from declared SVG units and may not reflect arbitrary nested SVG scaling; checks do not detect all clipping, overlaps, glyph fallback, contrast or PDF renderer differences.",
    }


def audit_scene_geometry(scene: dict) -> dict:
    """Detect pairwise node overlaps in a manually positioned scene.

    This is a conservative axis-aligned bounding-box check. It does not measure
    text glyph bounds, edge crossings, or intentional overlap semantics.
    """
    canvas = scene["canvas"]
    nodes = scene["nodes"]
    overlaps = []
    for index, left in enumerate(nodes):
        lx, ly = float(left["x_mm"]), float(left["y_mm"])
        lw, lh = float(left["width_mm"]), float(left["height_mm"])
        for right in nodes[index + 1:]:
            rx, ry = float(right["x_mm"]), float(right["y_mm"])
            rw, rh = float(right["width_mm"]), float(right["height_mm"])
            if lx < rx + rw and lx + lw > rx and ly < ry + rh and ly + lh > ry:
                overlaps.append([left["id"], right["id"]])
    issues = ["node_overlap"] if overlaps else []
    return {
        "within_canvas": all(
            float(node["x_mm"]) >= 0 and float(node["y_mm"]) >= 0
            and float(node["x_mm"]) + float(node["width_mm"]) <= float(canvas["width_mm"])
            and float(node["y_mm"]) + float(node["height_mm"]) <= float(canvas["height_mm"])
            for node in nodes
        ),
        "overlapping_node_pairs": overlaps,
        "issues": issues,
        "limitations": "Axis-aligned node bounds only; no text measurement, edge-crossing or intentional-overlap analysis.",
    }
