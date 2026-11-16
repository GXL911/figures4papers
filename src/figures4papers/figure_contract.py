"""Explicit scientific contract describing what the figure purports to show."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Literal

ChartType = Literal["grouped_bar", "learning_curves", "heatmap", "reliability", "other"]

@dataclass(frozen=True)
class FigureContract:
    figure_id: str
    chart_type: ChartType
    takeaway: str
    source_description: str
    x_unit: str
    y_unit: str
    uncertainty_kind: str = "none"
    provenance_note: str = ""
    uncertainty_by_metric: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.chart_type not in ("grouped_bar", "learning_curves", "heatmap", "reliability", "other"):
            raise ValueError("Unknown chart_type.")
        for name in ("figure_id", "takeaway", "source_description"):
            if not getattr(self, name).strip():
                raise ValueError(f"FigureContract.{name} cannot be blank.")
        atomic_kinds = {"sd", "sem", "ci", "bootstrap_ci", "bounds"}
        if self.uncertainty_kind not in atomic_kinds | {"none", "mixed"}:
            raise ValueError("Unknown uncertainty kind.")
        if self.uncertainty_kind == "mixed":
            if (len(set(self.uncertainty_by_metric.values())) < 2
                    or any(not metric.strip() or kind not in atomic_kinds
                           for metric, kind in self.uncertainty_by_metric.items())):
                raise ValueError("Mixed uncertainty requires at least two explicit metric-specific conventions.")
        elif self.uncertainty_by_metric:
            raise ValueError("Metric-specific uncertainty requires uncertainty_kind='mixed'.")
        object.__setattr__(self, "uncertainty_by_metric", dict(self.uncertainty_by_metric))

    def to_dict(self) -> dict:
        return asdict(self)
