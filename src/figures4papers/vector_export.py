"""Validated export for SVG-native diagrams and composed vector figures."""
from __future__ import annotations
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image

from .figure_contract import FigureContract
from .provenance import build_manifest


def export_svg(svg: str, out_path: str | Path, *, formats=("svg", "pdf", "png"),
               dpi: int = 300, contract: FigureContract | None = None,
               source_files=(), seed: int | None = None, transformations=()) -> list[Path]:
    """Export one SVG scene. PNG/PDF conversion requires the `illustration` extra."""
    if not isinstance(svg, str) or not svg.strip():
        raise ValueError("svg must be a nonempty string.")
    root = ET.fromstring(svg)
    if not root.tag.endswith("svg"):
        raise ValueError("Input document is not an SVG root.")
    if dpi < 72:
        raise ValueError("dpi must be >= 72.")
    if source_files and contract is None:
        raise ValueError("source_files requires a FigureContract.")
    if isinstance(formats, str):
        formats = (formats,)
    formats = tuple(str(fmt).lower().lstrip(".") for fmt in formats)
    if not formats or len(set(formats)) != len(formats) or any(f not in {"svg", "pdf", "png"} for f in formats):
        raise ValueError("formats must be unique members of svg/pdf/png.")
    target = Path(out_path)
    base = target.with_suffix("") if target.suffix.lower() in {".svg", ".pdf", ".png"} else target
    base.parent.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    if any(fmt in {"pdf", "png"} for fmt in formats):
        try:
            import cairosvg
        except ImportError as exc:
            raise ImportError("PNG/PDF vector export requires `pip install -e '.[illustration]'`.") from exc
    for fmt in formats:
        path = base.with_suffix("." + fmt)
        if fmt == "svg":
            path.write_text(svg, encoding="utf-8")
        elif fmt == "png":
            cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(path), dpi=dpi)
            with Image.open(path) as image:
                image.verify()
        else:
            cairosvg.svg2pdf(bytestring=svg.encode("utf-8"), write_to=str(path))
            if not path.read_bytes().startswith(b"%PDF-"):
                raise RuntimeError("Vector PDF export failed validation.")
        if not path.is_file() or path.stat().st_size < 32:
            raise RuntimeError(f"Missing or empty vector export: {path}")
        saved.append(path)
    if contract is not None:
        manifest = build_manifest(contract=contract, source_files=source_files,
                                  output_files=saved, seed=seed,
                                  transformations=transformations)
        base.with_suffix(".manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return saved
