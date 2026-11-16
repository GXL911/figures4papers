"""Fail-fast numeric validation plus nonfatal plot diagnostics."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from matplotlib.container import BarContainer

class ValidationError(ValueError):
    """Scientifically invalid data or figure specification."""

@dataclass(frozen=True)
class ValidationIssue:
    level: str
    code: str
    message: str

def validate_numeric_array(values, *, ndim: int | None = None, name: str = "data", allow_nan: bool = False) -> np.ndarray:
    try:
        arr = np.asarray(values, dtype=float)
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"{name} must be numeric.") from exc
    if arr.size == 0 or (ndim is not None and arr.ndim != ndim):
        raise ValidationError(f"{name} must be nonempty with ndim={ndim}.")
    if np.isinf(arr).any() or (not allow_nan and np.isnan(arr).any()):
        raise ValidationError(f"{name} contains NaN or Inf.")
    return arr

def validate_grouped_inputs(categories, series, labels, *, yerr=None, uncertainty_kind=None) -> np.ndarray:
    if not categories or len(set(categories)) != len(categories):
        raise ValidationError("Categories must be nonempty and unique.")
    if not labels or len(set(labels)) != len(labels):
        raise ValidationError("Legend labels must be nonempty and unique.")
    values = validate_numeric_array(series, ndim=2, name="series")
    if values.shape != (len(labels), len(categories)):
        raise ValidationError("series shape must be (n_methods,n_categories).")
    if yerr is not None:
        errors = validate_numeric_array(yerr, ndim=2, name="yerr")
        if errors.shape != values.shape or (errors < 0).any():
            raise ValidationError("yerr must have matching shape and be nonnegative.")
        if uncertainty_kind not in ("sd", "sem", "ci", "bootstrap_ci", "bounds"):
            raise ValidationError("yerr requires explicit uncertainty_kind.")
    return values

def validate_intervals(mean, lower, upper) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y = validate_numeric_array(mean, name="mean")
    lo = validate_numeric_array(lower, name="lower")
    hi = validate_numeric_array(upper, name="upper")
    if not (y.shape == lo.shape == hi.shape) or np.any(lo > y) or np.any(y > hi):
        raise ValidationError("Expected equally-shaped lower <= mean <= upper.")
    return y, lo, hi

def validate_reliability(nominal, empirical) -> tuple[np.ndarray, np.ndarray]:
    n = validate_numeric_array(nominal, ndim=1, name="nominal")
    e = validate_numeric_array(empirical, ndim=1, name="empirical")
    if n.size != e.size or np.any(np.diff(n) <= 0):
        raise ValidationError("Nominal must be strictly increasing and lengths must match.")
    if np.any((n < 0) | (n > 1)) or np.any((e < 0) | (e > 1)):
        raise ValidationError("Coverage must lie in [0,1].")
    if np.any(np.diff(e) < -1e-12):
        raise ValidationError("Empirical coverage must be nondecreasing for nested intervals on a common sample.")
    return n, e

def validate_bar_artists(bars: BarContainer, expected, *, atol: float = 1e-10) -> None:
    """Check the drawn bar heights, not image pixels, against source plot values."""
    actual = np.array([p.get_height() for p in bars.patches], dtype=float)
    source = validate_numeric_array(expected, ndim=1, name="expected bar heights")
    if actual.shape != source.shape or not np.allclose(actual, source, rtol=1e-9, atol=atol):
        raise ValidationError("Drawn bar heights do not match plot data.")

def validate_line_artist(line, x, y, *, atol: float = 1e-10) -> None:
    expected_x = validate_numeric_array(x, ndim=1, name="source x")
    expected_y = validate_numeric_array(y, ndim=1, name="source y")
    xx = validate_numeric_array(line.get_xdata(), ndim=1, name="drawn x")
    yy = validate_numeric_array(line.get_ydata(), ndim=1, name="drawn y")
    if (xx.shape != expected_x.shape or yy.shape != expected_y.shape or
            not np.allclose(xx, expected_x, atol=atol) or
            not np.allclose(yy, expected_y, atol=atol)):
        raise ValidationError("Drawn line does not match plot data.")

def validate_figure(fig, *, require_axis_labels: bool = True, bar_zero_warning: bool = True) -> list[ValidationIssue]:
    """Check actual Matplotlib axes; warnings need human interpretation.

    This cannot prove absence of collisions or semantic validity of a chart.
    Human inspection at final print size remains mandatory.
    """
    issues: list[ValidationIssue] = []
    if not fig.axes:
        raise ValidationError("Figure contains no axes.")
    for i, ax in enumerate(fig.axes):
        if not ax.get_visible() or not ax.axison:
            continue
        if ax.get_label().startswith("<colorbar"):
            continue
        if ax.name != "rectilinear":
            continue
        for key, limits in (("x", ax.get_xlim()), ("y", ax.get_ylim())):
            arr = np.asarray(limits, dtype=float)
            if not np.isfinite(arr).all() or arr[0] == arr[1]:
                raise ValidationError(f"Invalid {key} limits in panel {i}.")
        if require_axis_labels and not ax.get_xlabel().strip():
            issues.append(ValidationIssue("warning", "missing_x_label", f"Panel {i} has no x-axis label."))
        if require_axis_labels and not ax.get_ylabel().strip():
            issues.append(ValidationIssue("warning", "missing_y_label", f"Panel {i} has no y-axis label."))
        if bar_zero_warning and any(isinstance(c, BarContainer) for c in ax.containers):
            if ax.get_ylim()[0] > 0:
                issues.append(ValidationIssue("warning", "truncated_bar_axis", f"Panel {i} bar y-axis starts above zero; justify or revise."))
    return issues
