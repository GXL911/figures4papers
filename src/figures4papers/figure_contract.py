"""Explicit scientific contract describing what the figure purports to show."""
from __future__ import annotations
from dataclasses import asdict, dataclass
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

    def __post_init__(self):
        if self.chart_type not in ("grouped_bar", "learning_curves", "heatmap", "reliability", "other"):
            raise ValueError("Unknown chart_type.")
        for name in ("figure_id", "takeaway", "source_description"):
            if not getattr(self, name).strip():
                raise ValueError(f"FigureContract.{name} cannot be blank.")
        if self.uncertainty_kind not in ("none", "sd", "sem", "ci", "bootstrap_ci", "bounds"):
            raise ValueError("Unknown uncertainty kind.")

    def to_dict(self) -> dict:
        return asdict(self)
