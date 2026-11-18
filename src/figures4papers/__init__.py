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
    validate_color_semantics,
)
from .provenance import file_sha256, build_manifest
from .design_tokens import (DesignTokens, FigurePreset, DEFAULT_TOKENS, SINGLE_COLUMN, DOUBLE_COLUMN, publication_context, rc_params)
from .diagram import DiagramCanvas, DiagramNode
from .composer import FigureComposer
from .vector_export import export_svg
from .visual_qa import audit_svg, audit_palette, contrast_ratio
from .reference_atlas import AtlasValidationError, PaperRecord, FigureRecord, SearchHit, ReferenceAtlas, reciprocal_rank_fusion
from .design_contracts import DesignContractError, validate_design_brief, validate_scene, render_scene_svg
from .drawio_export import scene_to_drawio_xml, export_drawio

__version__ = "0.3.0a1"
