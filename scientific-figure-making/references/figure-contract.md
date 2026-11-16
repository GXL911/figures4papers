# Figure contract and scientific claims

Before drawing, specify what a figure is intended to communicate.
Code: figures4papers.FigureContract.

Required:
- figure_id: stable unique identifier.
- chart_type: grouped_bar / learning_curves / heatmap / reliability / other.
- takeaway: claim or question expressed without overstatement.
- source_description: inspectable raw-data path or honest source explanation.
- x_unit and y_unit: measurable units, or empty if dimensionless.
- uncertainty_kind: none / sd / sem / ci / bootstrap_ci / bounds.
- provenance_note: estimand, group structure, or missing assumptions.

Questions to resolve:
1. What evidence supports the takeaway and what is not demonstrated?
2. What is the statistical unit (seed / sample / task / market / step)?
3. What definition does each error bar actually use?
4. Are any fields imputed, clipped or transformed? Where and why?
5. Does changing axes or normalization risk misinterpretation?
6. Are numeric values consistent with source plotting arrays?
7. Is the legend and text legible in the target publication dimensions?

The contract stores user-declared intent. It cannot verify the truth
of research claims or infer an estimand from labels alone.
