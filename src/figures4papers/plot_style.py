"""Portable publication style; no TeX or proprietary fonts required by default."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE",
    "green_2": "#AADCA9",
    "green_3": "#8BCF8B",
    "red_1": "#F6CFCB",
    "red_2": "#E9A6A1",
    "red_strong": "#B64342",
    "neutral": "#CFCECE",
    "highlight": "#FFD700",
    "teal": "#42949E",
    "violet": "#9A4D8E",
}
DEFAULT_COLORS = (
    PALETTE["blue_main"], PALETTE["green_3"], PALETTE["red_strong"],
    PALETTE["teal"], PALETTE["violet"], PALETTE["neutral"],
)

@dataclass(frozen=True)
class FigureStyle:
    """Size in pt for final output, not an automatic guarantee at arbitrary scale."""
    font_size: float = 11
    axes_linewidth: float = 1.2
    use_tex: bool = False
    font_family: tuple[str, ...] = ("DejaVu Sans", "Arial", "Helvetica", "sans-serif")

    def __post_init__(self):
        if self.font_size <= 0 or self.axes_linewidth <= 0:
            raise ValueError("Font size and axes linewidth must be positive.")

def apply_publication_style(style: FigureStyle | None = None) -> None:
    """Set pyplot defaults. Use mpl.rc_context() to avoid global cross-project changes."""
    style = style or FigureStyle()
    mpl.rcParams.update({
        "font.family": list(style.font_family),
        "font.size": style.font_size,
        "axes.linewidth": style.axes_linewidth,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "text.usetex": style.use_tex,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "savefig.facecolor": "white",
    })

def create_subplots(nrows: int = 1, ncols: int = 1, figsize=None, **kwargs):
    """Return (figure, flattened axes array) even for a single subplot."""
    if nrows < 1 or ncols < 1:
        raise ValueError("nrows and ncols must be positive.")
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)
    return fig, np.asarray(axes, dtype=object).reshape(-1)
