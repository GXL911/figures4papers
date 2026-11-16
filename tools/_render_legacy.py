"""Internal worker: run a trusted, checked-in case in its own disposable directory."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import runpy
import sys

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
import numpy as np

from figures4papers.layout_review import review_layout

# Explicit display-only source substitutions. Match the exact legacy strings.
TEX_LABELS = {
    r"\textit{Improvement}": "Improvement",
    r"$\texttt{RNAGenScape}$ \textbf{(ours)}": "RNAGenScape (ours)",
    r"$\texttt{OpenVaccine}~(+)$": "OpenVaccine (+)",
    r"$\texttt{OpenVaccine}~(-)$": "OpenVaccine (-)",
    r"$\texttt{Zebrafish}~(+)$": "Zebrafish (+)",
    r"$\texttt{Zebrafish}~(-)$": "Zebrafish (-)",
    r"$\texttt{Ribosome}~(+)$": "Ribosome (+)",
    r"$\texttt{Ribosome}~(-)$": "Ribosome (-)",
}
TEX_SCRIPTS = {
    "figure_Dispersion/plot_idea.py", "figure_Dispersion/plot_illustration.py",
    "figure_RNAGenScape/plot_comparison.py", "figure_RNAGenScape/plot_comparison_speed.py",
    "figure_RNAGenScape/plot_sweep.py", "figure_ophthal_review/plot_composition.py",
    "figure_ophthal_review/plot_trend.py",
}


def portable_source(relative: str, source: str) -> tuple[str, list[str]]:
    # Use one known font everywhere. No numerical, layout or marker settings changed.
    portable = source.replace("'helvetica'", "'DejaVu Sans'").replace('"helvetica"', '"DejaVu Sans"')
    portable = portable.replace("['Helvetica', 'Arial', 'DejaVu Sans']", "['DejaVu Sans']")
    changes = ["portability: use bundled DejaVu Sans"] if portable != source else []
    if relative in TEX_SCRIPTS:
        token = "['text.usetex'] = True"
        count = portable.count(token)
        portable = portable.replace(token, "['text.usetex'] = False")
        if count != 1:
            raise ValueError(f"Expected exactly one known legacy usetex switch in {relative}, got {count}")
        changes.append("portability: use MathText, not external LaTeX")
    if relative in {"figure_RNAGenScape/plot_comparison.py", "figure_RNAGenScape/plot_comparison_speed.py"}:
        for old, new in TEX_LABELS.items():
            # Also replaces the exact full-label checks in the script, preserving styling.
            portable = portable.replace(old, new)
        portable = portable.replace(r"$\texttt{RNAGenScape}$", "RNAGenScape")
        portable = portable.replace(r"\\%", "%")
        changes.append("portability: translate explicit TeX method/benchmark/percent labels")
    return portable, changes


def main(config_file: str) -> None:
    config = json.loads(Path(config_file).read_text(encoding="utf-8"))
    script = Path(config["script"]).resolve()
    os.chdir(script.parent)
    (script.parent / "figures").mkdir(exist_ok=True)
    sys.path.insert(0, str(script.parent))
    # No modification to original or already-published figures outside this directory.
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    layouts = {}
    original_savefig = Figure.savefig

    def audited_savefig(self, filename, *args, **kwargs):
        path = Path(filename).resolve()
        if path.parent != (script.parent / "figures"):
            raise ValueError(f"Unexpected legacy output destination: {path}")
        if path.suffix.lower() == ".png":
            if path.name in layouts:
                raise ValueError(f"Legacy script rewrote {path.name}")
            tight = kwargs.get("bbox_inches") == "tight"
            layouts[path.name] = review_layout(
                self, width_mm=config["widths"].get(path.name, 178),
                tight=tight, pad_inches=kwargs.get("pad_inches", 0.1),
            )
        return original_savefig(self, filename, *args, **kwargs)

    Figure.savefig = audited_savefig
    if config["seed"] is not None:
        np.random.seed(config["seed"])  # deterministic review seed for formerly unseeded geometry
    sys.argv = [str(script)]
    runpy.run_path(str(script), run_name="__main__")
    Path(config["layout"]).write_text(json.dumps(layouts, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
