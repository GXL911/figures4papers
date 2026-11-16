# Figure Benchmark Gallery — v0.2

These six figures are original benchmark examples for testing the new diagram, composition and physical-size workflows. They are inspired by design patterns in classic papers, but they do not copy paper artwork or reproduce reported measurements. All plotted values and toy images are synthetic and are labelled as such in the figures and manifests.

| Output | Inspired design pattern | Width |
|---|---|---:|
| `01_resnet_mechanism` | ResNet residual mechanism / shortcut path | 178 mm |
| `ablation_matrix` | SimCLR-style factorial ablation matrix | 89 mm |
| `03_selective_ssm_hardware` | Mamba-style selection and hardware dataflow | 178 mm |
| `qualitative_quantitative` | DINO-style visual map plus toy quantitative check | 178 mm |
| `05_nature_style_composite` | Multi-panel journal-style composition | 178 mm |
| `paired_seed_effect` | Paired seed-level comparison | 89 mm |

Generate all examples:

```bash
python -m pip install -e ".[dev,illustration]"
python -m figure_benchmark.run_all --out figure-benchmark/generated
```

Review the final PDF page widths and rasterized proofs (Poppler required):

```bash
python tools/review_v02_figure_benchmark.py figure-benchmark/generated \
  --review-out figure-benchmark/review
```

The contact sheet is a review aid, not a publication proof. Inspect each PDF at its actual target width and compare it with the target venue's instructions.
