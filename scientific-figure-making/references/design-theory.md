# Design Theory — Historical Upstream Observations

This file records patterns observed in the original `figure_*` scripts from Chen Liu's upstream repository. It is a historical catalog, not the normative v0.2 design specification.

Some upstream scripts use very wide canvases, large typography, manually truncated axes, and fixed color conventions. Those choices may be appropriate for their specific source figures but should not be copied as universal rules.

For new work, follow:
- [Scientific Figure Design System v0.2](design-system-v0.2.md) for physical dimensions, typography, color semantics, axes, statistical honesty and QA.
- [Common Patterns v0.2](common-patterns.md) for paired seeds, ablation, scaling, qualitative/quantitative and composite layouts.
- [Paper Figure Atlas](paper-figure-atlas.md) for source-backed case studies.

The upstream palette remains available in `plot_style.py` for compatibility with existing examples. New code should use semantic `DesignTokens` roles and state the meaning of each visual encoding in the legend or caption.
