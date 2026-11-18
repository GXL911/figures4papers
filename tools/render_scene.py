"""Render a validated Scene Graph to SVG and editable draw.io."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from figures4papers import (
    FigureContract,
    ReferenceAtlas,
    audit_scene_geometry,
    audit_svg,
    build_manifest,
    export_drawio,
    export_svg,
    render_scene_svg,
    validate_renderer_capabilities,
    validate_scene_against_brief,
)
from figures4papers.reference_atlas import _default_atlas_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="Output basename without extension")
    parser.add_argument("--brief", type=Path, help="Optional Design Brief to verify semantic traceability")
    parser.add_argument("--atlas", type=Path, default=_default_atlas_dir())
    args = parser.parse_args()

    scene = json.loads(args.scene.read_text(encoding="utf-8"))
    brief = None
    atlas = None
    if args.brief:
        brief = json.loads(args.brief.read_text(encoding="utf-8"))
        atlas = ReferenceAtlas.from_directory(args.atlas)
        validate_scene_against_brief(brief, scene, atlas=atlas)

    requested_formats = (
        brief.get("constraints", {}).get("output_formats", ["svg", "drawio"])
        if brief else ["svg", "drawio"]
    )
    supported_formats = {"svg", "drawio"}
    unsupported = set(requested_formats) - supported_formats
    if unsupported:
        raise NotImplementedError(
            f"Scene renderer does not yet produce requested formats: {sorted(unsupported)}"
        )
    if not requested_formats:
        raise ValueError("At least one output format must be requested.")
    if "svg" in requested_formats:
        validate_renderer_capabilities(scene, "svg")
    if "drawio" in requested_formats:
        validate_renderer_capabilities(scene, "drawio")
    minimum_font = (
        float(brief.get("constraints", {}).get("minimum_font_size_pt", 6.0))
        if brief else 6.0
    )
    svg = render_scene_svg(scene) if "svg" in requested_formats else None
    svg_qa = audit_svg(svg, min_font_pt=minimum_font) if svg is not None else None
    geometry_qa = audit_scene_geometry(scene)
    if svg_qa and svg_qa["issues"]:
        raise RuntimeError(f"SVG QA failed: {svg_qa['issues']}")
    if geometry_qa["issues"] or not geometry_qa["within_canvas"]:
        raise RuntimeError(f"Scene geometry QA failed: {geometry_qa}")

    contract = FigureContract(
        figure_id=scene["figure_id"],
        chart_type="other",
        takeaway=brief["intended_takeaway"] if brief else (scene.get("description") or scene["title"]),
        source_description=(
            f"Scene specification: {args.scene.as_posix()}"
            + (f"; Design Brief: {args.brief.as_posix()}" if args.brief else "")
        ),
        x_unit="mm",
        y_unit="mm",
        provenance_note="Deterministic rendering from a versioned Scene Graph and validated Design Brief.",
    )
    output_files = []
    if svg is not None:
        output_files.extend(export_svg(svg, args.out, formats=("svg",)))
    if "drawio" in requested_formats:
        output_files.append(export_drawio(scene, args.out.with_suffix(".drawio")))

    source_files = [args.scene]
    if args.brief:
        source_files.append(args.brief)
        for name in ("papers.jsonl", "figures.jsonl", "taxonomy.json"):
            path = args.atlas / name
            if path.is_file():
                source_files.append(path)

    manifest = build_manifest(
        contract=contract,
        source_files=source_files,
        output_files=output_files,
        transformations=(
            "Design Brief + Scene Graph -> semantic validation",
            "Scene Graph v1.0 -> DiagramCanvas SVG",
            "Scene Graph v1.0 -> editable draw.io mxGraph objects",
            "SVG structural/font QA + axis-aligned geometry QA",
        ),
        metadata={
            "brief_id": brief.get("brief_id") if brief else None,
            "scene_id": scene["figure_id"],
            "reference_bindings": brief.get("references", []) if brief else [],
            "qa": {"svg": svg_qa, "geometry": geometry_qa},
        },
    )
    manifest_path = args.out.with_suffix(".manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for path in [*output_files, manifest_path]:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
