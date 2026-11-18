# Changelog

## Unreleased — Research Figure Making v0.3 foundations

- Add a metadata-first Paper Figure Atlas with 16 provisional figure references from 16 papers; no third-party figure binaries are redistributed.
- Separate scientific intent, figure role, visual form, layout pattern and evidence type in a versioned taxonomy.
- Add fielded BM25 retrieval, hard metadata filters, soft structural ranking and Reciprocal Rank Fusion.
- Add an optional semantic-score hook without bundling a large CLIP runtime or model weights.
- Add an eight-query hand-curated retrieval development set and MRR, Recall@k and nDCG@k evaluation utilities.
- Add JSON Schemas and runtime validators for Scientific Figure Design Briefs and Scene Graphs.
- Add deterministic SVG rendering for manually positioned box/circle scenes and editable draw.io XML export.
- Add architecture and research-source documentation; clarify that ELK layout, CLIP runtime, PPTX export and full visual QA remain future work.

## Unreleased — Research Figure Making v0.2

- Add physical-size-aware DesignTokens and 89 mm / 178 mm presets.
- Add an SVG-native DiagramCanvas for original mechanism and architecture diagrams.
- Add FigureComposer for mixed SVG and Matplotlib multi-panel figures, including SVG ID namespacing.
- Add validated SVG/PDF/PNG vector export through the optional CairoSVG extra.
- Add SVG accessibility metadata, declared-font-size checks, contrast and grayscale-similarity diagnostics.
- Add paired-seed, factorial-ablation, scaling-efficiency and qualitative/quantitative templates.
- Add six original benchmark figures, including classic-paper-inspired visual grammars and a single-column size test.
- Add PDF page-width/text-boundary/raster-proof review at 89 mm and 178 mm.
- Add a paper figure atlas with original paper links and design lessons; no source artwork is redistributed.
- Clarify that upstream wide canvases, large fonts and manually tightened axes are historical examples, not universal rules.

## Unreleased — Phase 5

- Regenerate all 29 legacy plotting scripts without altering their source files.
- Keep both upstream throughput outputs under distinct replay paths.
- Add repeat-render checks, original-image diffs and CI regression against a portable baseline.
- Add 178 mm PDF width checks and seven case-study adaptations for review.
- Record metric-specific SD/SEM for published ImmunoStruct figure panels.
- Preserve reported MACL cohort sizes and plot RNAGenScape aggregate tables with explicit shared scales.
- Original paper plotting scripts and image outputs were not modified.

## 0.1.0 (feature branch, not released)

- Keep all original nine figure_* research directories.
- Add installable Python API: plot style, plotting primitives, statistics,
  figure contract, validation and export.
- Add SHA256 provenance manifests and PNG/PDF/SVG output checks.
- Add four visibly synthetic figure templates.
- Add pytest and Python 3.10/3.12 GitHub Actions validation.
- Add agent workflow, executable API, catalog and audit documentation.
- Add non-destructive adapters for ImmunoStruct IEDB means, MACL PubMedQA
  retention and RNAGenScape optimization success rates. Original statistical
  inputs are not independently remeasured.

Original paper plotting scripts and image outputs were not modified.
