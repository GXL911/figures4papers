"""Conservative Agg text checks at a specified physical placement width."""
from __future__ import annotations

from itertools import combinations
from math import isfinite

from matplotlib.text import Annotation, Text
from matplotlib.transforms import Bbox


def review_layout(fig, *, width_mm: float, min_pt: float = 6.0,
                  tight: bool = False, pad_inches: float = 0.06) -> dict:
    """Report small, colliding and canvas-overflowing text (not a visual certificate).

    Check actual rendered text, including legends and annotations, not just rcParams.
    Tight cropping uses the active Agg renderer. PDF/SVG may differ slightly.
    """
    if not all(isfinite(v) for v in (width_mm, min_pt, pad_inches)) or (
        width_mm <= 0 or min_pt <= 0 or pad_inches < 0
    ):
        raise ValueError("Require positive width_mm/min_pt and nonnegative padding.")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    if tight:
        frame = fig.get_tightbbox(renderer).padded(pad_inches).transformed(fig.dpi_scale_trans)
    else:
        frame = fig.bbox
    scale = width_mm / (frame.width / fig.dpi * 25.4)
    inactive = set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis, *([ax.zaxis] if hasattr(ax, "zaxis") else [])):
            lo, hi = sorted(axis.get_view_interval())
            if not ax.axison or not axis.get_visible():
                inactive.update((axis.label, axis.offsetText))
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                margin = 1e-8 * max(abs(hi - lo), 1e-12)
                if not ax.axison or not axis.get_visible() or not lo-margin <= tick.get_loc() <= hi+margin:
                    inactive.update((tick.label1, tick.label2))
    labels = []
    for artist in fig.findobj(match=Text):
        ax = artist.axes
        if artist in inactive or not artist.get_visible() or not artist.get_text().strip() or (
            ax is not None and not ax.get_visible()
        ):
            continue
        if isinstance(artist, Annotation) and artist.get_tightbbox(renderer) is None:
            continue
        # Text.get_window_extent deliberately excludes Annotation's arrow.
        box = Text.get_window_extent(artist, renderer)
        if not all(isfinite(p) for p in box.extents) or box.width <= 0 or box.height <= 0:
            continue
        if artist.get_clip_on() and artist.get_tightbbox(renderer) is None:
            continue
        labels.append((artist.get_text().replace("\n", " ")[:100], artist.get_fontsize() * scale, box))
    small = [{"text": label, "pt": round(pt, 2)} for label, pt, _ in labels if pt < min_pt - 1e-6]
    overflow = [
        label for label, _, b in labels
        if b.x0 < frame.x0 - 1 or b.y0 < frame.y0 - 1
        or b.x1 > frame.x1 + 1 or b.y1 > frame.y1 + 1
    ]
    collisions = []
    for (label_a, _, a), (label_b, _, b) in combinations(labels, 2):
        overlap = Bbox.intersection(a, b)
        if overlap is not None and (
            overlap.width > 1 and overlap.height > 1
            and overlap.width * overlap.height > 0.12 * min(a.width * a.height, b.width * b.height)
        ):
            collisions.append([label_a, label_b])
    return {
        "target_width_mm": width_mm, "min_font_pt": min_pt, "text_count": len(labels),
        "minimum_effective_pt": round(min((p for _, p, _ in labels), default=0), 2) if labels else None,
        "small_text": small, "outside_canvas": overflow, "text_overlap_candidates": collisions,
    }
