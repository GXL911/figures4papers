"""Run every original plot script, compare upstream references, and emit review evidence."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import warnings
import sys
import tempfile

import numpy as np
from PIL import Image, ImageChops

from _render_legacy import portable_source
from figures4papers.provenance import file_sha256

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Case:
    script: str
    outputs: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    seed: int | None = None

    @property
    def family(self):
        return self.script.split("/")[0]


def case(family, script, pngs, *, pdfs="", dependencies=(), seed=None):
    return Case(f"figure_{family}/{script}.py",
                tuple(f"{p}.png" for p in pngs.split()) + tuple(f"{p}.pdf" for p in pdfs.split()),
                dependencies, seed)


CASES = (
    case("Brainteaser", "plot_brute_force", "brute_force"),
    case("Brainteaser", "plot_correctness_by_category", "correctness_by_category"),
    case("Brainteaser", "plot_correctness_by_subcategory", "correctness_by_subcategory"),
    case("Brainteaser", "plot_rewriting", "rewriting"),
    case("Brainteaser", "plot_selfcorrection_math", "selfcorrection_math"),
    case("CellSpliceNet", "plot_ablation", "ablation"),
    case("CellSpliceNet", "plot_comparison", "comparison_human comparison_worm"),
    case("Cflows", "diffusion_swiss_roll", "diffusion_swiss_roll", seed=42),
    case("Cflows", "plot_comparison_Ablation", "figX_comparison_Ablation", pdfs="figX_comparison_Ablation"),
    case("Cflows", "plot_comparison_GeneRegulatory", "fig2_comparison_GeneRegulatory", pdfs="fig2_comparison_GeneRegulatory"),
    case("Cflows", "plot_comparison_Trajectory", "fig2_comparison_Trajectory", pdfs="fig2_comparison_Trajectory"),
    case("Dispersion", "plot_idea", "idea"),
    case("Dispersion", "plot_illustration", "illustration"),
    case("ImmunoStruct", "plot_bars", "bars_ablation_Cancer bars_ablation_IEDB bars_comparison_Cancer bars_comparison_IEDB",
         dependencies=("raw_data.py",)),
    case("MACL", "plot_exp_qa", "exp_qa_ablation exp_qa_ablation_SFTRL exp_qa_comparison exp_qa_learning_curves"),
    case("MACL", "plot_exp_sub", "exp_sub_ablation exp_sub_comparison exp_sub_learning_curves"),
    case("MACL", "plot_exp_task", "exp_task_ablation exp_task_comparison exp_task_learning_curves"),
    case("MACL", "plot_overview", "overview_panel_b overview_panel_d",
         dependencies=("plot_exp_qa.py", "plot_exp_sub.py", "plot_exp_task.py")),
    case("RNAGenScape", "plot_comparison", "results_comparison_optimization results_comparison_speed"),
    case("RNAGenScape", "plot_comparison_speed", "results_comparison_speed"),
    case("RNAGenScape", "plot_hole_manifold", "manifold_holes"),
    case("RNAGenScape", "plot_manifold", "manifold"),
    case("RNAGenScape", "plot_sweep", "results_sweep"),
    case("VIGIL", "plot_ablation", "ablation_curves"),
    case("VIGIL", "plot_comparison_radar", "comparison_radar"),
    case("VIGIL", "plot_concept", "concept"),
    case("VIGIL", "plot_posttraining", "comparison_posttraining"),
    case("ophthal_review", "plot_composition", "composition_heatmap"),
    case("ophthal_review", "plot_trend", "trend_by_month"),
)

# Explicit diagnostic placement widths. No journal's approval is implied.
SINGLE_COLUMN = {
    "idea.png", "manifold.png", "manifold_holes.png", "results_sweep.png",
    "results_comparison_speed.png", "selfcorrection_math.png",
}


def output_key(item, name):
    # The two RNA throughput scripts alias a path upstream. Keep their results separate.
    return f"{item.script.removesuffix('.py')}/{name}"


def raster(path: Path, temp: Path) -> Image.Image:
    if path.suffix == ".pdf":
        stem = temp / "pdf_preview"
        subprocess.run(["pdftoppm", "-singlefile", "-scale-to", "1200", "-png", str(path), str(stem)],
                       check=True, capture_output=True)
        path = stem.with_suffix(".png")
    # A checked-in 600-dpi figure is 100+ MP. Keep Pillow's hard limit and compare
    # RGB without allocating full-size copies for already opaque images.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)
        with Image.open(path) as src:
            if src.mode == "RGB":
                return src.copy()
            rgba = np.asarray(src.convert("RGBA"))
            if np.all(rgba[:, :, 3] == 255):
                return Image.fromarray(np.ascontiguousarray(rgba[:, :, :3]))
            rgba_im = Image.fromarray(rgba)
            white = Image.new("RGBA", rgba_im.size, "white")
            return Image.alpha_composite(white, rgba_im).convert("RGB")


def compare(left: Image.Image, right: Image.Image):
    # Normalized same-canvas comparison. Track size and aspect independently.
    norm = (384, 256)
    a = left.resize(norm, Image.Resampling.LANCZOS)
    b = right.resize(norm, Image.Resampling.LANCZOS)
    diff = np.asarray(ImageChops.difference(a, b))
    return {
        "reference_pixels": list(left.size), "rendered_pixels": list(right.size),
        "aspect_change": round(abs((right.width / right.height) / (left.width / left.height) - 1), 6),
        "rgb_mae": round(float(diff.mean() / 255), 6),
        "changed_pixels": round(float((diff.max(axis=2) > 24).mean()), 6),
    }, a, b, Image.fromarray(np.uint8(np.minimum(diff.astype("uint16") * 3, 255)))


def publication_review_image(im: Image.Image, width_mm, dpi=180):
    width = round(width_mm / 25.4 * dpi)
    height = max(1, round(im.height * width / im.width))
    return im.resize((width, height), Image.Resampling.LANCZOS), dpi


def run_case(item: Case, out: Path, *, mode: str, repeat: bool):
    row = {"script": item.script, "outputs": {}, "seed_override": item.seed,
           "source_sha256": {}, "transformations": []}
    try:
        with tempfile.TemporaryDirectory(prefix="figure-replay-") as d:
            temp = Path(d)
            script = ROOT / item.script
            for source in [script, *(script.with_name(n) for n in item.dependencies)]:
                relative = source.relative_to(ROOT).as_posix()
                row["source_sha256"][relative] = file_sha256(source)
                original = source.read_text(encoding="utf-8")
                code, changes = portable_source(relative, original) if mode == "portable" else (original, [])
                (temp / source.name).write_text(code, encoding="utf-8")
                row["transformations"].extend(f"{source.name}: {c}" for c in changes)
            config = temp / "config.json"
            config.write_text(json.dumps({
                "script": str(temp / script.name), "seed": item.seed,
                "widths": {p: 89 for p in item.outputs if p in SINGLE_COLUMN},
                "layout": str(temp / "layout.json"),
            }), encoding="utf-8")
            worker = [sys.executable, str(ROOT / "tools/_render_legacy.py"), str(config)]
            env = dict(os.environ, MPLBACKEND="Agg", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
            actual = temp / "figures"

            def run_once():
                process = subprocess.run(worker, cwd=temp, env=env, capture_output=True, text=True, timeout=120)
                if process.returncode:
                    raise RuntimeError(process.stderr[-4500:] or process.stdout[-4500:])
                paths = sorted(p.name for p in actual.iterdir())
                if paths != sorted(item.outputs):
                    raise ValueError(f"Unexpected output set: expected {sorted(item.outputs)}, got {paths}")
                return json.loads((temp / "layout.json").read_text(encoding="utf-8")), process.stderr[-2500:]

            layouts, notes = run_once()
            if repeat:
                actual.rename(temp / "first")
                run_once()
            for name in item.outputs:
                path = actual / name
                im = raster(path, temp)
                if repeat:
                    first = raster(temp / "first" / name, temp)
                    if first.size != im.size or ImageChops.difference(first, im).getbbox() is not None:
                        raise ValueError(f"Non-deterministic decoded render: {name}")
                key = output_key(item, name)
                work = out / "renders" / key
                work.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, work)
                record = {"sha256": file_sha256(work), "repeat_equal": True if repeat else None,
                          "layout": layouts.get(name)}
                upstream = ROOT / item.family / "figures" / name
                if upstream.is_file():
                    stats, a, b, delta = compare(raster(upstream, temp), im)
                    record.update(upstream_sha256=file_sha256(upstream), upstream_comparison=stats)
                    strip = Image.new("RGB", (3 * 384, 256), "white")
                    for i, tile in enumerate((a, b, delta)):
                        strip.paste(tile, (i * 384, 0))
                    p = out / "diffs" / (key + ".png")
                    p.parent.mkdir(parents=True, exist_ok=True)
                    strip.save(p)
                if name in layouts:
                    p = out / "publication-size" / key
                    p.parent.mkdir(parents=True, exist_ok=True)
                    preview, dpi = publication_review_image(im, layouts[name]["target_width_mm"])
                    preview.save(p, dpi=(dpi, dpi))
                row["outputs"][name] = record
            row.update(status="rendered", stderr=notes)
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError) as exc:
        row.update(status="failed", error=str(exc))
    return row


def check_baseline(rows, baseline: dict):
    # Baseline is a versioned, reviewed portable replay, not a claim of paper-image equality.
    from image_signature import signature, signature_delta
    errors = []
    observed = {output_key(Case(r["script"], ()), name): v for r in rows for name, v in r["outputs"].items()}
    for key in sorted(set(observed) | set(baseline)):
        if key not in baseline or key not in observed:
            errors.append(f"Unexpected or missing baseline key: {key}")
            continue
        old, new = baseline[key], observed[key]
        if new["layout"] is not None and old["layout_counts"] is not None:
            for check in ("outside_canvas", "small_text", "text_overlap_candidates"):
                if len(new["layout"][check]) > old["layout_counts"][check] + (1 if check == "small_text" else 0):
                    errors.append(f"{key}: worsened layout diagnostic {check}")
        delta = signature_delta(old["signature"], new["signature"])
        if delta["mae"] > .012 or delta["changed_tiles"] > .06 or delta["aspect"] > .015:
            errors.append(f"{key}: portable render changed {delta}")
    return errors


def main():
    from image_signature import signature
    import matplotlib
    import scipy
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "review/generated")
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=2)
    parser.add_argument("--mode", choices=("portable", "native"), default="portable")
    parser.add_argument("--repeat", action="store_true", help="Rerender separately and require equal decoded pixels")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--baseline", type=Path)
    group.add_argument("--write-baseline", type=Path, help="Record a new baseline for explicit review")
    args = parser.parse_args()
    if args.mode != "portable" and (args.baseline or args.write_baseline):
        parser.error("Versioned baseline is for portable mode only")
    args.out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda item: run_case(item, args.out, mode=args.mode, repeat=args.repeat), CASES))
    all_outputs = {}
    with tempfile.TemporaryDirectory() as tmp:
        for item, row in zip(CASES, rows):
            for name, rec in row["outputs"].items():
                key = output_key(item, name)
                rec["signature"] = signature(raster(args.out / "renders" / key, Path(tmp)))
                all_outputs[key] = {
                    "signature": rec["signature"],
                    "layout_counts": {k: len(rec["layout"][k]) for k in
                                      ("outside_canvas", "small_text", "text_overlap_candidates")}
                    if rec["layout"] is not None else None,
                }
    failed = [row["script"] for row in rows if row["status"] != "rendered"]
    regression_errors = check_baseline(rows, json.loads(args.baseline.read_text(encoding="utf-8"))) if args.baseline else []
    if args.write_baseline and not failed:
        args.write_baseline.write_text(json.dumps(all_outputs, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "mode": args.mode, "repeat": args.repeat,
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "matplotlib": matplotlib.__version__, "scipy": scipy.__version__},
        "rendered_scripts": len(rows) - len(failed), "total_scripts": len(rows),
        "outputs": len(all_outputs),
        "upstream_comparisons": sum("upstream_comparison" in v for row in rows for v in row["outputs"].values()),
        "regression_errors": regression_errors, "cases": rows,
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for row in rows:
        print(f"{row['status']:8} {row['script']} ({len(row['outputs'])} outputs)", flush=True)
        if row["status"] == "failed":
            print(row["error"], flush=True)
    for error in regression_errors:
        print(error)
    print(f"{report['rendered_scripts']}/{report['total_scripts']} scripts; {len(all_outputs)} exports; "
          f"{report['upstream_comparisons']} upstream comparisons; {len(regression_errors)} regressions")
    return int(bool(failed or regression_errors))


if __name__ == "__main__":
    raise SystemExit(main())
