"""Physical-size-aware design tokens for publication figures.

Tokens are defaults, not universal journal rules. Always inspect the exported
figure at its intended final width and follow the target venue's instructions.
"""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
import math

import matplotlib as mpl
from matplotlib.colors import is_color_like
from cycler import cycler


@dataclass(frozen=True)
class FigurePreset:
    name: str
    width_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        if (not self.name.strip() or not all(math.isfinite(v) and v > 0 for v in (self.width_mm, self.height_mm))):
            raise ValueError("A preset needs a name and positive physical dimensions.")

    @property
    def figsize_inches(self) -> tuple[float, float]:
        return self.width_mm / 25.4, self.height_mm / 25.4


@dataclass(frozen=True)
class DesignTokens:
    font_family: tuple[str, ...] = ("DejaVu Sans", "sans-serif")
    font_size_pt: float = 9.0
    axes_label_pt: float = 9.0
    tick_label_pt: float = 8.0
    legend_pt: float = 8.0
    panel_label_pt: float = 9.0
    title_pt: float = 10.0
    axes_linewidth_pt: float = 0.7
    data_linewidth_pt: float = 1.5
    marker_size_pt: float = 3.5
    grid_linewidth_pt: float = 0.45
    panel_gap_mm: float = 4.0
    outer_margin_mm: float = 3.0
    background: str = "#FFFFFF"
    foreground: str = "#20242A"
    muted: str = "#68717D"
    grid: str = "#D9DEE5"
    proposed: str = "#245A8D"
    baseline: str = "#C46A45"
    secondary: str = "#3C8D86"
    accent: str = "#8A6BBE"
    neutral: str = "#A7ADB5"

    def __post_init__(self) -> None:
        numeric = (self.font_size_pt, self.axes_label_pt, self.tick_label_pt,
                   self.legend_pt, self.panel_label_pt, self.title_pt,
                   self.axes_linewidth_pt, self.data_linewidth_pt,
                   self.marker_size_pt, self.grid_linewidth_pt,
                   self.panel_gap_mm, self.outer_margin_mm)
        if any(not math.isfinite(value) or value <= 0 for value in numeric):
            raise ValueError("Design token dimensions must be finite and positive.")
        if not self.font_family:
            raise ValueError("font_family cannot be empty.")
        if any(not is_color_like(color) for color in self.colors.values()):
            raise ValueError("Every design token color must be a valid color.")

    @property
    def colors(self) -> dict[str, str]:
        return {
            "background": self.background, "foreground": self.foreground,
            "muted": self.muted, "grid": self.grid, "proposed": self.proposed,
            "baseline": self.baseline, "secondary": self.secondary,
            "accent": self.accent, "neutral": self.neutral,
        }


DEFAULT_TOKENS = DesignTokens()
SINGLE_COLUMN = FigurePreset("single-column-89mm", 89.0, 62.0)
DOUBLE_COLUMN = FigurePreset("double-column-178mm", 178.0, 112.0)


def rc_params(tokens: DesignTokens = DEFAULT_TOKENS) -> dict:
    return {
        "font.family": list(tokens.font_family),
        "font.size": tokens.font_size_pt,
        "axes.labelsize": tokens.axes_label_pt,
        "xtick.labelsize": tokens.tick_label_pt,
        "ytick.labelsize": tokens.tick_label_pt,
        "legend.fontsize": tokens.legend_pt,
        "axes.titlesize": tokens.title_pt,
        "axes.linewidth": tokens.axes_linewidth_pt,
        "lines.linewidth": tokens.data_linewidth_pt,
        "lines.markersize": tokens.marker_size_pt,
        "grid.linewidth": tokens.grid_linewidth_pt,
        "text.color": tokens.foreground,
        "axes.labelcolor": tokens.foreground,
        "xtick.color": tokens.foreground,
        "ytick.color": tokens.foreground,
        "axes.edgecolor": tokens.foreground,
        "axes.prop_cycle": cycler(color=[tokens.proposed, tokens.baseline, tokens.secondary, tokens.accent, tokens.neutral]),
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "figure.facecolor": tokens.background,
        "axes.facecolor": tokens.background,
        "savefig.facecolor": tokens.background,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "text.usetex": False,
    }


@contextmanager
def publication_context(tokens: DesignTokens = DEFAULT_TOKENS):
    """Temporarily apply the design system without leaking global rcParams."""
    with mpl.rc_context(rc=rc_params(tokens)):
        yield
