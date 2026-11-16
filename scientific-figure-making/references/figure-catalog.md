# Figure catalog — all upstream Python scripts

Static review baseline 2026-11-16: commit 0ddfbd3fc989. The 30 Python
files include one raw_data.py and 29 plotting scripts. Upstream outputs
are case-study references, **not certified by fork v0.1 tests**.

| Project | Script | Scientific figure role |
| --- | --- | --- |
| Brainteaser | plot_brute_force.py | composition / brute-force distribution |
| Brainteaser | plot_correctness_by_category.py | grouped categorical result |
| Brainteaser | plot_correctness_by_subcategory.py | subgroup performance |
| Brainteaser | plot_rewriting.py | rewriting comparisons |
| Brainteaser | plot_selfcorrection_math.py | self-correction experiment |
| CellSpliceNet | plot_ablation.py | component ablation |
| CellSpliceNet | plot_comparison.py | multi-metric bars with SD |
| Cflows | diffusion_swiss_roll.py | diffusion geometry |
| Cflows | plot_comparison_Ablation.py | ablation, PDF/PNG |
| Cflows | plot_comparison_GeneRegulatory.py | regulatory comparisons, PDF/PNG |
| Cflows | plot_comparison_Trajectory.py | trajectory comparisons, PDF/PNG |
| Dispersion | plot_idea.py | seeded synthetic geometry |
| Dispersion | plot_illustration.py | geometric conceptual panels |
| ImmunoStruct | plot_bars.py | comparisons and ablative bars |
| ImmunoStruct | raw_data.py | original hard-coded metrics and error arrays |
| MACL | plot_exp_qa.py | QA learning/retention across training stages |
| MACL | plot_exp_sub.py | subdiscipline learning/retention |
| MACL | plot_exp_task.py | mixed-task learning/retention |
| MACL | plot_overview.py | combined retention panels |
| RNAGenScape | plot_comparison.py | optimization comparison and heatmap |
| RNAGenScape | plot_comparison_speed.py | speed / log-scale bars |
| RNAGenScape | plot_hole_manifold.py | manifold holes |
| RNAGenScape | plot_manifold.py | manifold concept |
| RNAGenScape | plot_sweep.py | hyperparameter curves |
| VIGIL | plot_ablation.py | data fraction and hyperparameters |
| VIGIL | plot_comparison_radar.py | nonuniform normalized radar |
| VIGIL | plot_concept.py | counterfactual concept and KDE |
| VIGIL | plot_posttraining.py | post-training comparison |
| ophthal_review | plot_composition.py | clinical category heatmap |
| ophthal_review | plot_trend.py | cumulative trend, event labels |

Reusable design references: ImmunoStruct for multi-metric comparison;
MACL for long-horizon learning/retention; RNAGenScape for annotated
heatmaps; Dispersion and VIGIL for geometric explanatory figures.

Migration order: ImmunoStruct -> MACL -> RNAGenScape, maintaining original
script and artifact snapshots, tracing statistics, comparing actual plotted
numbers, and reviewing rendered images at publication size.
