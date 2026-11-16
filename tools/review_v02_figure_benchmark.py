"""Check benchmark PDF physical widths, text bounds and rasterized proofs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw

EXPECTED_WIDTH_MM = {
    "01_resnet_mechanism.pdf": 178.0,
    "03_selective_ssm_hardware.pdf": 178.0,
    "05_nature_style_composite.pdf": 178.0,
    "ablation_matrix.pdf": 89.0,
    "paired_seed_effect.pdf": 89.0,
    "qualitative_quantitative.pdf": 178.0,
}


def review_one(pdf: Path, preview: Path, expected_mm: float) -> dict:
    raw = subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"], text=True)
    root = ET.fromstring(raw)
    pages = root.findall(".//{*}page")
    if len(pages) != 1:
        raise ValueError(f"{pdf.name}: expected one page, got {len(pages)}")
    page = pages[0]
    width_pt, height_pt = float(page.get("width")), float(page.get("height"))
    width_mm = width_pt * 25.4 / 72
    if abs(width_mm - expected_mm) > 0.25:
        raise ValueError(f"{pdf.name}: expected {expected_mm} mm, got {width_mm:.3f} mm")
    words = page.findall(".//{*}word")
    if not words:
        raise ValueError(f"{pdf.name}: no extractable text")
    outside = []
    for word in words:
        bounds = [float(word.get(k)) for k in ("xMin", "yMin", "xMax", "yMax")]
        if bounds[0] < -0.75 or bounds[1] < -0.75 or bounds[2] > width_pt + 0.75 or bounds[3] > height_pt + 0.75:
            outside.append(word.text or "")
    if outside:
        raise ValueError(f"{pdf.name}: text outside page: {outside[:8]}")

    preview.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "180", "-singlefile", "-png", str(pdf),
                    str(preview.with_suffix(""))], check=True, capture_output=True)
    with Image.open(preview) as image:
        rgb = image.convert("RGB")
        if rgb.width < 100 or rgb.height < 100 or (rgb.convert("L").getextrema()[0] > 245):
            raise ValueError(f"{pdf.name}: raster proof is blank or too small")
        pixel_size = rgb.size
    return {"expected_width_mm": expected_mm, "actual_width_mm": round(width_mm, 3),
            "page_height_mm": round(height_pt * 25.4 / 72, 3),
            "extractable_words": len(words), "out_of_page_words": outside,
            "raster_pixels": list(pixel_size)}


def run(root: Path, review_out: Path) -> dict:
    report = {}
    tiles = []
    for filename, expected_width in EXPECTED_WIDTH_MM.items():
        pdf = root / filename
        if not pdf.is_file():
            raise FileNotFoundError(pdf)
        preview = review_out / (pdf.stem + ".png")
        report[filename] = review_one(pdf, preview, expected_width)
        with Image.open(preview) as image:
            tile = image.convert("RGB")
            tile.thumbnail((760, 500), Image.Resampling.LANCZOS)
            tiles.append((filename, tile.copy()))
    columns = 2
    rows = (len(tiles) + columns - 1) // columns
    contact = Image.new("RGB", (1600, rows * 540), "#EEF1F4")
    draw = ImageDraw.Draw(contact)
    for index, (label, tile) in enumerate(tiles):
        x, y = (index % columns) * 800 + 20, (index // columns) * 540 + 20
        draw.text((x, y), label, fill="#20242A")
        contact.paste(tile, (x, y + 22))
    review_out.mkdir(parents=True, exist_ok=True)
    contact.save(review_out / "contact-sheet.png")
    (review_out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Directory containing benchmark PDFs")
    parser.add_argument("--review-out", type=Path, default=Path("figure-benchmark-review"))
    args = parser.parse_args()
    result = run(args.root, args.review_out)
    print(f"Reviewed {len(result)} PDFs at their declared 89/178 mm widths")
