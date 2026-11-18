"""Render a manual Scene Graph to SVG and editable draw.io."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from figures4papers import FigureContract, export_drawio, export_svg, render_scene_svg, validate_scene_against_brief


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="Output basename without extension")
    parser.add_argument("--brief", type=Path, help="Optional Design Brief to verify semantic traceability")
    args = parser.parse_args()
    scene = json.loads(args.scene.read_text(encoding="utf-8"))
    if args.brief:
        brief = json.loads(args.brief.read_text(encoding="utf-8"))
        validate_scene_against_brief(brief, scene)
    svg = render_scene_svg(scene)
    contract = FigureContract(
        figure_id=scene["figure_id"],
        chart_type="other",
        takeaway=scene.get("description") or scene["title"],
        source_description=f"Scene specification: {args.scene.as_posix()}",
        x_unit="mm",
        y_unit="mm",
        provenance_note="Deterministic SVG rendering from a versioned Scene Graph.",
    )
    svg_paths = export_svg(
        svg, args.out, formats=("svg",), contract=contract,
        source_files=(args.scene,),
        transformations=("Scene Graph v1.0 -> DiagramCanvas SVG",),
    )
    drawio_path = export_drawio(scene, args.out.with_suffix(".drawio"))
    for path in [*svg_paths, drawio_path, args.out.with_suffix(".manifest.json")]:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
