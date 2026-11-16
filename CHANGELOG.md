# Changelog

## Unreleased — Phase 5

- Regenerate all 29 legacy plotting scripts without altering their source files.
- Keep both upstream throughput outputs under distinct replay paths.
- Add repeat-render checks, original-image diffs and CI regression against a portable baseline.
- Add 178 mm PDF width checks and seven case-study adaptations for review.
- Record metric-specific SD/SEM for published ImmunoStruct figure panels.
- Preserve reported MACL cohort sizes and plot RNAGenScape aggregate tables with explicit shared scales.

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
