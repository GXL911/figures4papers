"""Statistical summaries for independent replication runs.

No silent uncertainty inference. For correlated time-series data, choose an
appropriate block/hierarchical resampling scheme outside summarize_seeds.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.stats import t as t_distribution

UncertaintyKind = Literal["none", "sd", "sem", "ci", "bootstrap_ci"]

@dataclass(frozen=True)
class UncertaintySpec:
    kind: UncertaintyKind
    confidence_level: float | None = None
    n_resamples: int = 2000
    seed: int = 0
    independent_replicates: bool = True

    def __post_init__(self):
        if self.kind in ("ci", "bootstrap_ci"):
            if self.confidence_level is None or not (0 < self.confidence_level < 1):
                raise ValueError("CI requires confidence_level in (0,1).")
        elif self.confidence_level is not None:
            raise ValueError("confidence_level only applies to CIs.")
        if self.n_resamples < 100 and self.kind == "bootstrap_ci":
            raise ValueError("Bootstrap CI requires at least 100 resamples.")
        if not self.independent_replicates:
            raise ValueError("This API supports independent replicates only; use block/hierarchical bootstrap for dependent data.")

@dataclass(frozen=True)
class Summary:
    mean: np.ndarray
    lower: np.ndarray | None
    upper: np.ndarray | None
    n: int
    kind: str
    confidence_level: float | None

def summarize_seeds(samples, spec: UncertaintySpec, *, axis: int = 0) -> Summary:
    """Summarize arrays with one independent random seed per row (axis)."""
    x = np.asarray(samples, dtype=float)
    if x.ndim < 1 or not x.size or not np.isfinite(x).all():
        raise ValueError("samples must be a nonempty finite numeric array.")
    axis = np.core.numeric.normalize_axis_index(axis, x.ndim)
    n = x.shape[axis]
    if spec.kind != "none" and n < 2:
        raise ValueError("Uncertainty needs at least two independent replicates.")
    mean = np.mean(x, axis=axis)
    if spec.kind == "none":
        return Summary(mean, None, None, n, spec.kind, None)
    sd = np.std(x, axis=axis, ddof=1)
    if spec.kind == "sd":
        delta = sd
    elif spec.kind == "sem":
        delta = sd / np.sqrt(n)
    elif spec.kind == "ci":
        delta = t_distribution.ppf((1 + spec.confidence_level) / 2, n - 1) * sd / np.sqrt(n)
    elif spec.kind == "bootstrap_ci":
        rng = np.random.default_rng(spec.seed)
        x = np.moveaxis(x, axis, 0)
        indices = rng.integers(n, size=(spec.n_resamples, n))
        boot_mean = x[indices].mean(axis=1)
        tail = (1 - spec.confidence_level) / 2
        return Summary(mean, np.quantile(boot_mean, tail, axis=0),
                       np.quantile(boot_mean, 1-tail, axis=0),
                       n, spec.kind, spec.confidence_level)
    else:
        raise ValueError(f"Unknown uncertainty kind: {spec.kind}")
    return Summary(mean, mean - delta, mean + delta, n, spec.kind, spec.confidence_level)
