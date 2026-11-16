# Figure Composer

`FigureComposer` combines SVG-native diagrams and Matplotlib figures into one SVG/PDF/PNG multi-panel figure with a fixed physical width.

```python
from figures4papers.composer import FigureComposer
from figures4papers.diagram import DiagramCanvas
from figures4papers import FigureContract

left = DiagramCanvas(80, 55, title="Mechanism")
left.add_box("input", 4, 20, 18, 14, "Input")
left.add_box("operator", 34, 20, 28, 14, "Memory operator")
left.add_arrow((22, 27), (34, 27), element_id="input-to-operator")

composer = FigureComposer(width_mm=178, columns=2, panel_height_mm=66,
                          title="Mechanism and evidence")
composer.add_svg_panel(left.to_svg(), label="(a)", title="Architecture")
composer.add_matplotlib_panel(experiment_figure, label="(b)", title="Controlled result")
composer.export("figures/composite", formats=("svg", "pdf", "png"),
    contract=FigureContract("composite", "other", "Connect the mechanism to controlled evidence",
                            "Source experiment data and original vector diagram", "panel", "mixed units"))
```

## Layout behavior

- Grid order is row-major.
- The caller chooses panel labels, titles, column count, panel height and gaps.
- SVG panels must provide a `viewBox`.
- Matplotlib panels are serialized to SVG with panel-specific SVG ID salts.
- Element IDs are prefixed on insertion to avoid collisions between panels.
- The output canvas uses millimetres and is exported at the requested width.

The composer is intentionally deterministic and conservative. It does not infer a good panel order, crop semantically important content, solve arbitrary text collisions, or guarantee that a dense panel remains legible after scaling. Design each panel for its allocated cell and inspect the exported PDF.
