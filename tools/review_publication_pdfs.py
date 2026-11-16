"""Inspect final PDF exports using Poppler rather than relying on Agg alone."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw


def audit_one(pdf: Path, png: Path, expected_mm: float):
    details = subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"], text=True)
    root = ET.fromstring(details)
    pages = root.findall(".//{*}page")
    if len(pages) != 1:
        raise ValueError(f"{pdf.name}: expected one PDF page, got {len(pages)}")
    page = pages[0]
    width, height = (float(page.get(k)) for k in ("width", "height"))
    actual_mm = width * 25.4 / 72
    if abs(actual_mm - expected_mm) > .1:
        raise ValueError(f"{pdf.name}: PDF is {actual_mm:.3f} mm wide, expected {expected_mm}")
    words = page.findall(".//{*}word")
    if not words:
        raise ValueError(f"{pdf.name}: no extractable PDF text")
    bad = [word.text for word in words if
           (float(word.get("xMin")) < -.5 or float(word.get("yMin")) < -.5 or
            float(word.get("xMax")) > width + .5 or float(word.get("yMax")) > height + .5)]
    if bad:
        raise ValueError(f"{pdf.name}: PDF word boxes outside page: {bad}")
    png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "180", "-singlefile", "-png", str(pdf),
                    str(png.with_suffix(""))], check=True, capture_output=True)
    with Image.open(png) as im:
        gray = np.asarray(im.convert("L"))
        if (gray < 230).mean() < .001:
            raise ValueError(f"{pdf.name}: rasterized PDF is blank or almost blank")
    return {"width_mm": round(actual_mm, 4), "words": len(words), "out_of_page_words": bad}


def run(root: Path):
    collection = {"immunostruct": 4, "macl": 1, "rnagenscape": 2}
    preview = root / "publication-pdf-review"
    audit = {}
    tiles = []
    for folder, count in collection.items():
        pdfs = sorted((root / folder).glob("*.pdf"))
        if len(pdfs) != count:
            raise ValueError(f"{folder}: expected {count} PDFs, got {len(pdfs)}")
        for pdf in pdfs:
            png = preview / folder / (pdf.stem + ".png")
            audit[f"{folder}/{pdf.name}"] = audit_one(pdf, png, 178)
            with Image.open(png) as im:
                tile = im.convert("RGB")
                tile.thumbnail((520, 320), Image.Resampling.LANCZOS)
                tiles.append((f"{folder} / {pdf.stem}", tile))
    result = Image.new("RGB", (1120, 370 * ((len(tiles)+1)//2)), "#f3f5f7")
    draw = ImageDraw.Draw(result)
    for index, (label, tile) in enumerate(tiles):
        x, y = index % 2 * 560 + 20, index // 2 * 370 + 20
        draw.text((x, y), label, fill="#17314d")
        result.paste(tile, (x, y+20))
    result.save(preview / "contact-sheet.png")
    (preview / "report.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    print(f"Verified physical width and rasterized {len(run(parser.parse_args().root))} PDFs")
