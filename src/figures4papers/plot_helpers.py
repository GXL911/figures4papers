"""Validated Matplotlib primitives. Never synthesize error bars silently."""
from __future__ import annotations
import numpy as np
from matplotlib import colors as mcolors
from matplotlib.patches import Circle

from .plot_style import DEFAULT_COLORS, PALETTE
from .figure_validation import (
    ValidationError, validate_numeric_array, validate_grouped_inputs,
    validate_intervals, validate_bar_artists, validate_line_artist,
    validate_reliability,
)

def annotate_bars(ax, bars, fmt="{:.2f}", fontsize=9, padding=3):
    """Annotate bar containers with their exact plotted heights."""
    for bar in bars:
        height = bar.get_height()
        if not np.isfinite(height):
            raise ValidationError("Cannot annotate nonfinite bar.")
        ax.annotate(fmt.format(height), xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, padding if height >= 0 else -padding),
                    textcoords="offset points", ha="center",
                    va="bottom" if height >= 0 else "top", fontsize=fontsize)

def make_grouped_bar(ax, categories, series, labels, ylabel="Value", colors=None,
                     annotate=False, *, yerr=None, uncertainty_kind=None):
    """Return one BarContainer per method, validating plotted numeric values.

    yerr must be nonnegative and must declare sd/sem/ci/bootstrap_ci/bounds.
    CI input here is half-width, not raw lower/upper endpoints.
    """
    categories, labels = list(categories), list(labels)
    values = validate_grouped_inputs(categories, series, labels,
                                    yerr=yerr, uncertainty_kind=uncertainty_kind)
    errors = np.asarray(yerr, dtype=float) if yerr is not None else None
    palette = list(colors) if colors is not None else list(DEFAULT_COLORS)
    if len(palette) < len(labels):
        raise ValidationError("Provide at least one color per method.")
    x = np.arange(len(categories))
    width = 0.8 / len(labels)
    containers = []
    for i, label in enumerate(labels):
        err = errors[i] if errors is not None else None
        container = ax.bar(x - 0.4 + width*(i + 0.5), values[i],
                           width=width, color=palette[i], label=label,
                           yerr=err, capsize=3 if err is not None else 0,
                           edgecolor="#333333", linewidth=0.4)
        validate_bar_artists(container, values[i])
        containers.append(container)
        if annotate:
            annotate_bars(ax, container)
    ax.set_xticks(x, categories)
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    return containers

def make_learning_curves(ax, x, means, labels, *, lower=None, upper=None,
                         uncertainty_kind=None, colors=None, xlabel="Step",
                         ylabel="Metric", alpha=0.16):
    """Plot (n_methods,n_steps), optionally with explicitly-specified intervals."""
    xs = validate_numeric_array(x, ndim=1, name="x")
    if np.any(np.diff(xs) <= 0):
        raise ValidationError("x must be strictly increasing.")
    values = validate_numeric_array(means, ndim=2, name="means")
    labels = list(labels)
    if values.shape != (len(labels), len(xs)):
        raise ValidationError("Expected means shape (n_methods,n_steps).")
    if (lower is None) != (upper is None):
        raise ValidationError("lower and upper must be specified together.")
    if lower is not None:
        if uncertainty_kind not in ("sd", "sem", "ci", "bootstrap_ci", "bounds"):
            raise ValidationError("Explicit uncertainty_kind required for shaded bands.")
        _, low, high = validate_intervals(values, lower, upper)
    else:
        if uncertainty_kind is not None:
            raise ValidationError("uncertainty_kind provided without intervals.")
        low = high = None
    palette = list(colors) if colors is not None else list(DEFAULT_COLORS)
    if len(palette) < len(labels):
        raise ValidationError("Insufficient colors.")
    lines = []
    for i, label in enumerate(labels):
        line, = ax.plot(xs, values[i], label=label, linewidth=2, color=palette[i])
        validate_line_artist(line, xs, values[i])
        lines.append(line)
        if low is not None:
            ax.fill_between(xs, low[i], high[i], color=palette[i], alpha=alpha,
                            linewidth=0)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    return lines

def make_trend(ax, x, y_series, labels, colors=None, ylabel=None, xlabel=None,
               show_shadow=False, *, lower=None, upper=None, uncertainty_kind=None):
    """Compatibility wrapper; a shadow requires real interval data."""
    if show_shadow and (lower is None or upper is None):
        raise ValidationError("show_shadow=True requires lower/upper uncertainty data.")
    return make_learning_curves(ax, x, y_series, labels, colors=colors,
                                ylabel=ylabel or "Value", xlabel=xlabel or "Step",
                                lower=lower, upper=upper,
                                uncertainty_kind=uncertainty_kind)

def make_heatmap(ax, matrix, x_labels=None, y_labels=None, cmap="viridis",
                 cbar_label=None, annotate=False, *, allow_nan=False, vmin=None,
                 vmax=None):
    """Dense 2D heatmap; missing values require explicit allow_nan=True."""
    values = validate_numeric_array(matrix, ndim=2, name="matrix", allow_nan=allow_nan)
    ny, nx = values.shape
    if x_labels is not None and len(x_labels) != nx:
        raise ValidationError("x_labels length differs from number of columns.")
    if y_labels is not None and len(y_labels) != ny:
        raise ValidationError("y_labels length differs from number of rows.")
    data = np.ma.masked_invalid(values) if allow_nan else values
    image = ax.imshow(data, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(np.arange(nx), x_labels if x_labels is not None else
                  [str(i) for i in range(nx)])
    ax.set_yticks(np.arange(ny), y_labels if y_labels is not None else
                  [str(i) for i in range(ny)])
    if annotate:
        norm = image.norm
        colormap = image.cmap
        for r in range(ny):
            for c in range(nx):
                if np.isnan(values[r, c]):
                    continue
                rgba = colormap(norm(values[r, c]))
                luminance = 0.2126*rgba[0] + 0.7152*rgba[1] + 0.0722*rgba[2]
                ax.text(c, r, f"{values[r,c]:.2f}", ha="center", va="center",
                        color="black" if luminance > 0.5 else "white", fontsize=9)
    colorbar = ax.figure.colorbar(image, ax=ax)
    if cbar_label:
        colorbar.set_label(cbar_label)
    return image

def make_scatter(ax, x, y, label=None, color=None, size=50, alpha=0.7):
    xx = validate_numeric_array(x, ndim=1, name="x")
    yy = validate_numeric_array(y, ndim=1, name="y")
    if len(xx) != len(yy):
        raise ValidationError("x/y length mismatch.")
    return ax.scatter(xx, yy, label=label, color=color or PALETTE["blue_main"],
                      s=size, alpha=alpha)

def make_sphere_illustration(ax, light_dir=(-0.5, 0.5, 0.8), resolution=128, alpha=0.6):
    """Shaded hemisphere projection; conceptual illustration, not 3D data."""
    if resolution < 32:
        raise ValidationError("resolution must be >=32.")
    light = validate_numeric_array(light_dir, ndim=1, name="light_dir")
    if len(light) != 3 or np.linalg.norm(light) == 0:
        raise ValidationError("light_dir must be a nonzero 3-vector.")
    light = light / np.linalg.norm(light)
    yy, xx = np.mgrid[-1:1:complex(resolution), -1:1:complex(resolution)]
    radius2 = xx**2 + yy**2
    zz = np.sqrt(np.maximum(0, 1-radius2))
    intensity = np.clip(0.3 + 0.7*(xx*light[0] + yy*light[1] + zz*light[2]), 0, 1)
    mask = np.ma.masked_where(radius2 > 1, intensity)
    ax.imshow(mask, cmap="Greys_r", extent=(-1,1,-1,1), origin="lower", alpha=alpha)
    ax.add_patch(Circle((0,0), 1, fill=False, color="#777777", linewidth=0.7))
    ax.set_aspect("equal")
    ax.axis("off")
    return ax

def make_reliability_diagram(ax, nominal, empirical, *, lower=None, upper=None,
                             uncertainty_kind=None, label="Empirical coverage",
                             color=None):
    """Coverage calibration for nested intervals on the same evaluation sample."""
    n, e = validate_reliability(nominal, empirical)
    if (lower is None) != (upper is None):
        raise ValidationError("lower and upper must be provided together.")
    if lower is not None:
        if uncertainty_kind not in ("ci", "bootstrap_ci", "bounds"):
            raise ValidationError("Coverage intervals require CI/Bootstrap CI/bounds type.")
        _, low, high = validate_intervals(e, lower, upper)
        if np.any(low < 0) or np.any(high > 1):
            raise ValidationError("Coverage interval must be in [0,1].")
    else:
        low = high = None
    ax.plot([0,1], [0,1], color="#777777", linestyle="--", linewidth=1,
            label="Perfect calibration")
    line, = ax.plot(n, e, color=color or PALETTE["blue_main"], marker="o",
                    linewidth=2, label=label)
    validate_line_artist(line, n, e)
    if low is not None:
        ax.fill_between(n, low, high, alpha=0.17, color=color or PALETTE["blue_main"])
    ax.set(xlim=(0,1), ylim=(0,1), xlabel="Nominal coverage",
           ylabel="Empirical coverage")
    ax.set_aspect("equal", adjustable="box")
    ax.legend(frameon=False)
    return line
