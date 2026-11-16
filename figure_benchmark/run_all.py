"""Generate six original benchmark figures for human publication review."""
from __future__ import annotations
import argparse
from pathlib import Path

from .resnet_mechanism import build as resnet
from .mamba_hardware import build as mamba
from .nature_composite import build as composite
from templates.ablation_matrix import build as simclr
from templates.qualitative_quantitative import build as dino
from templates.paired_seed_effect import build as paired_seed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("figure_benchmark/generated"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    results = [resnet(args.out), simclr(args.out), mamba(args.out), dino(args.out),
               composite(args.out), paired_seed(args.out)]
    images = [path for paths, _ in results for path in paths]
    for ext in ("png", "pdf", "svg"):
        count = sum(path.suffix == f".{ext}" for path in images)
        if count != 6:
            raise SystemExit(f"Expected 6 {ext} exports, found {count}")
    manifests = list(args.out.glob("*.manifest.json"))
    if len(manifests) != 6:
        raise SystemExit(f"Expected 6 manifests, found {len(manifests)}")
    print(f"Generated {len(images)} figure exports and {len(manifests)} manifests in {args.out}")


if __name__ == "__main__":
    main()
