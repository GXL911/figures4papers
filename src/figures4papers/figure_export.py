"""Consistent, checked PNG/PDF/SVG export with optional SHA256 manifest."""
from __future__ import annotations
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image

from .figure_contract import FigureContract
from .provenance import build_manifest

SUPPORTED_FORMATS = {"pdf", "svg", "eps", "png", "jpg", "jpeg", "tif", "tiff"}

def _check_export(path: Path) -> None:
    if not path.is_file() or path.stat().st_size < 32:
        raise RuntimeError(f"Missing or empty export: {path}")
    suffix = path.suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
        with Image.open(path) as im:
            im.verify()
    elif suffix == ".pdf":
        if not path.read_bytes().startswith(b"%PDF-"):
            raise RuntimeError(f"Invalid PDF header: {path}")
    elif suffix == ".svg":
        root = ET.parse(path).getroot()
        if not root.tag.endswith("svg"):
            raise RuntimeError(f"Invalid SVG root: {path}")
    elif suffix == ".eps":
        if not path.read_bytes().startswith(b"%!PS"):
            raise RuntimeError(f"Invalid EPS header: {path}")

def finalize_figure(fig, out_path, formats=None, dpi: int = 300, close: bool = True,
                    pad: float = 0.06, *, contract: FigureContract | None = None,
                    source_files=(), seed: int | None = None, transformations=(),
                    crop: bool = True):
    """Write each format; optionally emit a provenance manifest.

    Return paths to image files (manifest path is base.with_suffix('.manifest.json')).
    Pass crop=False to preserve the canvas physical dimensions instead of tight cropping.
    Import Matplotlib with Agg backend for headless scripts before pyplot import.
    """
    import matplotlib.pyplot as plt

    if dpi < 72 or pad < 0:
        raise ValueError("DPI must be >=72 and padding nonnegative.")
    if source_files and contract is None:
        raise ValueError("source_files requires an explicit FigureContract.")
    target = Path(out_path)
    if formats is None:
        formats = (target.suffix.lstrip(".").lower(),) if target.suffix else ("png", "pdf", "svg")
    if isinstance(formats, str):
        formats = (formats,)
    formats = tuple(f.lower().lstrip(".") for f in formats)
    if not formats or len(set(formats)) != len(formats) or any(f not in SUPPORTED_FORMATS for f in formats):
        raise ValueError("Unsupported or duplicate export formats.")
    base = target.with_suffix("") if target.suffix.lower().lstrip(".") in SUPPORTED_FORMATS else target
    base.parent.mkdir(parents=True, exist_ok=True)
    saved = []
    try:
        for fmt in formats:
            path = base.with_suffix("." + fmt)
            fig.savefig(path, format=fmt, dpi=dpi, bbox_inches="tight" if crop else fig.bbox_inches, pad_inches=pad)
            _check_export(path)
            saved.append(path)
        if contract is not None:
            manifest = build_manifest(contract=contract, source_files=source_files,
                                      output_files=saved, seed=seed, transformations=transformations)
            base.with_suffix(".manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        elif source_files:
            raise ValueError("source_files requires an explicit FigureContract.")
    finally:
        if close:
            plt.close(fig)
    return saved
