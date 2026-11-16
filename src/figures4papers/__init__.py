"""Reproducible, publication-oriented scientific figures.

This implementation is an independent extension of the figures4papers
case-study repository; original figure_* scripts remain unmodified.
"""
from .plot_style import FigureStyle, PALETTE, DEFAULT_COLORS, apply_publication_style, create_subplots
from .plot_helpers import (
    make_grouped_bar, annotate_bars, make_learning_curves, make_trend,
    make_heatmap, make_scatter, make_reliability_diagram,
)
from .figure_export import finalize_figure
from .figure_contract import FigureContract
from .statistics import UncertaintySpec, Summary, summarize_seeds
from .figure_validation import (
    ValidationError, ValidationIssue, validate_numeric_array,
    validate_grouped_inputs, validate_intervals, validate_figure,
    validate_bar_artists, validate_line_artist, validate_reliability,
)
from .provenance import file_sha256, build_manifest

__version__ = "0.1.0"
