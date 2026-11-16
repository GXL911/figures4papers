# Common Patterns for Publication Figures — v0.2

These are conditional design patterns, not rules to apply mechanically. Start with the scientific claim and final physical dimensions. See [design-system-v0.2.md](design-system-v0.2.md) for the normative design system.

## Paired seed comparison

Use when methods share the same independent random seeds or experimental replicates. Connect each matched pair, show the per-seed differences, and report a clearly named summary interval. Do not discard pairing by showing unrelated bars. Do not treat time points within one run as independent seeds.

## Factorial ablation matrix

Use a heatmap when rows and columns are meaningful experimental factors and the cells represent valid combinations. Fix and disclose the color scale. If the matrix is asymmetric, do not imply symmetry. Include the actual numeric values when exact comparisons matter.

## Scaling and efficiency

Separate quality from cost when they have different units. Use log axes only when the multiplicative scale is scientifically meaningful, label them, and show the measured range. Avoid dual axes that imply a direct numerical comparison between unrelated quantities.

## Qualitative plus quantitative evidence

Show the input, model-derived output, and a clearly described overlay or comparison. Pair it with a metric computed under a stated threshold or criterion. Label illustrative examples and representative-case selection.

## Architecture and mechanism diagrams

Use the diagram engine for simple vector primitives and dataflow. Keep one visual grammar for inputs, operations, state, outputs and control paths. Explain simplifications. For a complicated graph, use a dedicated layout tool rather than forcing it into a manually positioned row of boxes.

## Multi-panel composites

Use the composer for fixed-width SVG/PDF/PNG composition. Make the reading order explicit, use panel labels consistently, and do not shrink panels just to fit a grid. If panel content becomes too dense, change the grid or make a separate figure.

## Historical patterns that are not defaults

The upstream case-study scripts contain useful examples of wide canvases, large typography, manually adjusted axes and dedicated legend panels. These are observations about those scripts, not universal recommendations. In particular, do not default to ultra-wide canvases, crop y-axes automatically, or apply the same font size regardless of final physical width.
