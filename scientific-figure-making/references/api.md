# Executable Figure Making API — Fork v0.1

This fork supplies a real Python implementation in src/figures4papers;
the upstream reference originally described functions to implement.
The original figure_* scripts are preserved and are not yet migrated.

## Install and execute

    python -m pip install -e ".[dev]"
    python -m pytest -q
    python examples/run_all.py --out examples/generated

Import from figures4papers. See templates/ for complete, executable examples.

## Publication style

- FigureStyle(font_size=11, axes_linewidth=1.2, use_tex=False)
- apply_publication_style(style=None): configure Matplotlib rcParams.
- create_subplots(nrows=1,ncols=1,figsize=None,**kwargs): (fig, flat_axes).
- PALETTE and DEFAULT_COLORS: original figure blue/green/red colors.

Defaults avoid LaTeX and prefer portable sans-serif fallback. Final font
size must be evaluated at the paper's actual physical dimensions.

## Plot primitives

- make_grouped_bar(ax, categories, series, labels, ylabel='Value',
  colors=None, annotate=False, *, yerr=None, uncertainty_kind=None)
  Series shape: (n_methods,n_categories). Returns a list of BarContainers,
  one per method. With yerr you MUST specify sd/sem/ci/bootstrap_ci/bounds.
  CI yerr denotes nonnegative half-width around the shown point estimate.
- annotate_bars(ax, bars, fmt='{:.2f}', fontsize=9, padding=3).
- make_learning_curves(ax,x,means,labels,*,lower=None,upper=None,
  uncertainty_kind=None, colors=None, xlabel='Step', ylabel='Metric').
  All curves have shape (n_methods,n_steps). Shaded bands require actual
  supplied bounds; the function never guesses a standard deviation.
- make_trend(ax,x,y_series,labels,...,show_shadow=False,*,lower=None,
  upper=None,uncertainty_kind=None): thin learning-curves wrapper.
  show_shadow=True without explicit bounds fails.
- make_heatmap(ax,matrix,x_labels=None,y_labels=None,cmap='viridis',
  cbar_label=None,annotate=False,*,allow_nan=False,vmin=None,vmax=None).
  Missing cells require allow_nan=True.
- make_scatter(ax,x,y,label=None,color=None,size=50,alpha=0.7).
- make_sphere_illustration(ax,light_dir=(-0.5,0.5,0.8),resolution=128,
  alpha=0.6): illustrative shading; not measured 3D geometry.
- make_reliability_diagram(ax,nominal,empirical,*,lower=None,upper=None,
  uncertainty_kind=None,label='Empirical coverage',color=None).
  Both arrays in [0,1], nominal strictly ascending. Coverage CIs must
  be explicitly provided, with a declared kind.

## Statistical summaries

Use UncertaintySpec(kind='ci',confidence_level=0.95) with
summarize_seeds(samples,spec,axis=0). The return value contains mean,
lower, upper, n, kind and confidence_level.

Available kinds: none, sd, sem, ci (Student-t), bootstrap_ci (seeded
percentile bootstrap). ONLY independent replicate axes are supported.
For time-series observations use separately justified dependence-aware
block/hierarchical resampling.

## Validation and provenance

- validate_numeric_array(data,ndim=None,name='data',allow_nan=False)
- validate_grouped_inputs(categories,series,labels,yerr=None,uncertainty_kind=None)
- validate_intervals(mean,lower,upper)
- validate_reliability(nominal,empirical)
- validate_bar_artists(container,expected): check Matplotlib bar heights.
- validate_line_artist(line,x,y): check plotted x/y arrays.
- validate_color_semantics(fig): warn when a series changes colors across panels.
- validate_figure(fig): report warning diagnostics about axis labels,
  truncated bar axes and invalid limits. Manual visual review is required.

The FigureContract dataclass declares figure_id, chart_type, takeaway,
source_description, x_unit, y_unit, uncertainty_kind and provenance_note.

finalize_figure(fig,out_path,formats=('png','pdf','svg'),dpi=300,
close=True,pad=0.06,contract=None,source_files=(),seed=None,
transformations=()) checks file integrity and optionally writes a
filename.manifest.json with SHA256 hashes of sources and outputs.

Be honest: a SHA256 hash establishes file identity, not the correctness
of a scientific experiment or of arbitrary data transformations.

See figure-contract.md, statistical-visualization.md, data-provenance.md,
figure-catalog.md, and the executable templates.
