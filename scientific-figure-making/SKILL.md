---
name: scientific-figure-making
description: >-
  Creates publication-oriented scientific data figures, SVG mechanism diagrams,
  and composed multi-panel figures using this repository's validated Python API.
  Use for academic papers, conference submissions, research reports and figure
  review. Not for interactive dashboards, web visualizations, primary 3D/GIS
  workflows, or Illustrator/Figma-first artwork.
---

# Scientific Figure Making

## v0.2 capability map

The repository now has three complementary paths:

1. **Data visualization** — Matplotlib statistical and experimental figures.
2. **Scientific illustration** — SVG-native diagrams through `DiagramCanvas`.
3. **Figure composition** — SVG and Matplotlib panels combined by `FigureComposer`.

The v0.2 defaults are physical-size-aware. They are not a guarantee of journal
acceptance; always follow the target venue's instructions.

## Mandatory workflow

1. **Scientific question:** state the claim this figure is intended to support.
2. **Evidence contract:** identify source files, units, experimental unit,
   baseline, metric and uncertainty convention.
3. **Visual grammar:** choose architecture/mechanism, comparison, paired seeds,
   ablation matrix, scaling, distribution, qualitative/quantitative, or a
   multi-panel composite. Do not choose a chart type for decoration.
4. **Physical layout:** choose 89 mm or 178 mm (or the actual venue width) before
   finalizing fonts, panel count and annotations.
5. **Construct:** use Matplotlib for data; `DiagramCanvas` for simple vector
   mechanisms; `FigureComposer` for mixed SVG/Matplotlib panels.
6. **Validate:** numeric arrays, statistical metadata, plotted artists, SVG IDs,
   declared font sizes, palette contrast and provenance.
7. **Export:** vector PDF/SVG for text and shapes; PNG for raster images and
   review proofs. Install the `illustration` extra for SVG-to-PDF/PNG rendering.
8. **Review:** inspect the actual PDF at its final physical width, check text
   bounds, rasterize a proof, and perform human scientific/visual review.

## Install and run

```bash
python -m pip install -e ".[dev,illustration]"
python -m pytest -q
python examples/run_all.py --out examples/generated
python -m figure_benchmark.run_all --out figure-benchmark/generated
```

With Poppler installed, review benchmark PDFs at their declared widths:

```bash
python tools/review_v02_figure_benchmark.py figure-benchmark/generated \
  --review-out figure-benchmark/review
```

## References to load

- `references/api.md`: installed package API and v0.2 entry points.
- `references/design-system-v0.2.md`: physical dimensions, type, color, axes,
  statistical honesty and QA.
- `references/diagram-engine.md`: SVG mechanism diagram API and limitations.
- `references/figure-composer.md`: mixed vector/data panel composition.
- `references/paper-figure-atlas.md`: ResNet, SimCLR, Mamba, DINO and a recent
  Nature Communications case study.
- `references/figure-contract.md`: claim, source, units and uncertainty.
- `references/statistical-visualization.md`: statistical conventions.
- `references/data-provenance.md`: SHA256 manifests and their limitations.
- `references/figure-catalog.md`: original upstream Python demonstrations.

## Non-negotiable scientific constraints

- Never invent source measurements, uncertainty intervals or missing values.
- Never treat synthetic benchmark values as published paper results.
- Do not infer SD/SEM/CI from arbitrary arrays; declare and justify the method.
- Preserve pairing and the true independent experimental unit.
- Do not treat autocorrelated time points as independent replicates.
- Do not automatically truncate axes or change source values to improve visual
  appearance.
- A file hash proves file identity, not the correctness of an experiment.
- Automated layout diagnostics are not a visual certificate. Human review is
  required before publication.

## When not to use

- Plotly, Altair, Bokeh or other interactive/web-first visualization.
- Exploratory-only EDA without a publication target.
- Primary 3D, GIS or geographic mapping.
- Complex hand-illustrated artwork whose main workflow belongs in a dedicated
  vector editor. Exported SVG can still be composed when appropriate.
