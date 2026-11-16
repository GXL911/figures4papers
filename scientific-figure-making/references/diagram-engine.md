# Diagram Engine

The v0.2 diagram engine creates original, editable SVG vector diagrams without requiring a browser or a proprietary illustration application.

## API

```python
from figures4papers.diagram import DiagramCanvas
from figures4papers import FigureContract
from figures4papers.vector_export import export_svg

canvas = DiagramCanvas(178, 82, title="Residual learning mechanism",
                       description="Identity shortcut plus learned residual branch.")
canvas.add_box("input", 5, 30, 25, 16, "Input", subtitle="x")
canvas.add_box("residual", 45, 18, 48, 40, "Residual function", subtitle="F(x)")
canvas.add_circle("sum", 110, 38, 7, label="+")
canvas.add_box("output", 130, 30, 28, 16, "Output", subtitle="y")
canvas.add_arrow((30, 38), (45, 38), element_id="input-to-residual")
canvas.add_arrow((93, 38), (103, 38), element_id="residual-to-sum")
canvas.add_arrow((117, 38), (130, 38), element_id="sum-to-output")

contract = FigureContract("residual-block", "other",
    "The shortcut is added to the residual function", "Original explanatory diagram",
    "not applicable", "not applicable")
export_svg(canvas.to_svg(), "figures/residual_block",
           formats=("svg", "pdf", "png"), contract=contract)
```

Install the optional renderer for PDF/PNG conversion:

```bash
python -m pip install -e ".[illustration]"
```

## Coordinate and validation contract

- Canvas dimensions and coordinates are millimetres.
- `font_size_pt` and `width_pt` arguments are points.
- IDs must be unique within a canvas.
- Shapes must fit inside the declared canvas.
- Text is XML-escaped; do not pass untrusted SVG fragments as labels.
- `to_svg()` returns a complete SVG document with title, role and viewBox.

The engine supports boxes, circles, text, straight lines and arrows. It is not a full diagram editor, auto-layout solver, graph router, or TeX renderer. Complex curves, detailed illustrations, and exact paper-specific art may need a specialized vector editor or a separate renderer.
