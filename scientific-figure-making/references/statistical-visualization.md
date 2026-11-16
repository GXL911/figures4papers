# Statistical and visual validation

Use explicit and correct semantics for uncertainty:

- SD: sample standard deviation with ddof=1.
- SEM: SD / sqrt(n independent replicates).
- CI: Student-t confidence interval over independent replicates.
- Bootstrap CI: seeded percentile interval over independent replicates.
- Bounds: arbitrary supplied interval, not necessarily a confidence interval.

Never silently create shading around a single deterministic line.
Missing arrays should fail by default; heatmap can deliberately mask NaN
values with allow_nan=True. Incorrect dimensions, negative error bar
magnitudes and unacknowledged uncertainty should cause errors.

Avoid treating electricity/time-series observations as independent
replications when there is serial dependence. Choose an explicit block
bootstrap or a defensible hierarchical unit outside this basic API.

Numeric validation covers source arrays and selected Matplotlib artists.
Visual validation warns about missing axis labels, invalid axis limits
and truncated bar charts, but it **cannot reliably detect** every text
overlap, colorblind ambiguity or misleading interpretation. Inspect
each exported figure at actual paper size.

Passing a figure_validation check does not prove an original paper's
raw experimental values were reproduced. Keep data provenance separately.
