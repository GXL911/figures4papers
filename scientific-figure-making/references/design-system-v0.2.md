# Scientific Figure Design System v0.2

This document defines defaults for the fork's new figure system. They are starting points, not universal journal rules. The target venue's instructions and the scientific task take precedence.

## 1. Design from final physical size

Use physical dimensions rather than designing at an arbitrary screen size and shrinking at the end.

| Preset | Width | Intended use |
|---|---:|---|
| `SINGLE_COLUMN` | 89 mm | One compact plot, small matrix, paired effect plot |
| `DOUBLE_COLUMN` | 178 mm | Multi-panel figure, architecture plus evidence, dense comparisons |

The presets provide convenient starting heights. Change the height to suit the visual grammar and content. Export without tight cropping (`crop=False`) when the requested physical canvas width is part of the publication contract.

Recommended initial type scale at final size:
- Main panel title: 9–10 pt.
- Axis labels and legend: 8–9 pt.
- Tick labels and dense annotations: 7–8 pt.
- Panel labels: 8–9 pt, bold.
- Below 6 pt: treat as a warning that needs explicit justification and manual review, not an automatic universal failure.

Do not scale a 178 mm figure to 89 mm and assume it remains publication-ready. Create a separate single-column layout when necessary.

## 2. Semantic color and redundant encoding

`DesignTokens` exposes roles rather than assigning colors by arbitrary order:
- `proposed`: focal method or proposed mechanism.
- `baseline`: comparator or reference condition.
- `secondary`: a distinct supporting series.
- `accent`: a single additional category or mechanism.
- `neutral`: uncertainty, context, or secondary observations.

The palette is not a claim that green means improvement or red means failure. State the mapping in the legend or caption. Use markers, line styles, labels, position, or hatching as redundant encodings; do not make color the only way to distinguish important series. Check the actual background and grayscale proof.

## 3. Axes and statistical honesty

- Bar charts should normally start at zero. If a nonzero baseline is essential, disclose it clearly and do not hide it in an automatic helper.
- A line chart may use a focused y-range when the absolute range is not the scientific question, but the limits must be visible and defensible.
- Do not auto-truncate axes to amplify a difference.
- Label the unit and the metric. Use percentage points versus relative percent correctly.
- Name the uncertainty convention: SD, SEM, confidence interval, bootstrap interval, or an explicitly defined bound.
- For seed-based ML experiments, plot individual independent seeds when the sample size is small. Preserve pairing when methods share seeds.
- Do not treat temporally autocorrelated time points as independent replicates. Use a justified block, hierarchical, or dependence-aware procedure.
- A heatmap is appropriate for a meaningful two-dimensional design or matrix, not merely to decorate a one-dimensional comparison.

## 4. Mechanism diagrams

Use the SVG `DiagramCanvas` for vector-native boxes, labels, arrows and simple shapes. Coordinates are millimetres on the final canvas; font sizes and line width arguments are points. Give each semantic element a stable unique ID.

A good mechanism diagram should identify:
1. Inputs and outputs.
2. The operations that transform information.
3. Branches, skip connections, state updates, or data movement.
4. The mathematical relationship when it is central to the claim.
5. What has intentionally been simplified.

Avoid unnecessary gradients, pseudo-3D effects, decorative icons, and text inside boxes that cannot be read at the final width. Use external vector tools or pre-rendered equation SVG for complex mathematical notation; the built-in engine is deliberately not a TeX typesetting system.

## 5. Figure composition

`FigureComposer` lays out existing SVG and Matplotlib panels in a physical-size grid. It does not decide the scientific reading order for the author.
- Panel order should follow the argument, not the order in which scripts ran.
- Align panel headings, axes, and repeated legends consistently.
- Use a shared legend only when the mapping is genuinely shared.
- Do not shrink dense panels to fit a predetermined grid. Change the grid or create a dedicated layout.
- Keep panel labels and panel titles distinct from data labels.
- Include a caption-level statement of what the full multi-panel figure proves and what each panel contributes.

## 6. Export and quality assurance

Prefer vector PDF/SVG for lines, text, diagrams and charts. Use raster PNG for pixel-based images and review previews. Raster output should be generated at the intended physical size and resolution (300 dpi is a common starting point, not a universal requirement).

Run all of the following:
1. Numeric and statistical validation on the source data.
2. Artist-level checks that plotted values match the supplied values.
3. SVG structure, duplicate-ID and declared-font-size diagnostics.
4. Palette contrast and grayscale-similarity screening.
5. PDF page-size, text-boundary and rasterized-proof checks.
6. Human inspection at 89 mm or 178 mm as actually intended.

Automated checks are diagnostics. They cannot prove that a chart is scientifically valid, that labels are semantically correct, or that no visual ambiguity exists.
