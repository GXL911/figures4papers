# Paper Figure Atlas — v0.2

This atlas records design patterns from influential papers. It links to the original papers and describes what to learn; it does not redistribute paper figures, datasets, or author artwork. Benchmark examples in this repository are new vector illustrations and explicitly synthetic data, not reproductions.

## 1. ResNet — scientific argument and mechanism

**He et al., “Deep Residual Learning for Image Recognition,” CVPR 2016.**
[Official CVF paper](https://openaccess.thecvf.com/content_cvpr_2016/papers/He_Deep_Residual_Learning_CVPR_2016_paper.pdf)

- Figure 1: use training and test error together to distinguish degradation from a story that would be explained by generalization alone.
- Figure 2: isolate the residual block so the identity path and learned branch are visually unambiguous.
- Figure 4: compare plain and residual networks under matched depth/parameter considerations rather than presenting an unqualified leaderboard.

Reusable pattern: observation → mechanism → controlled comparison.

## 2. SimCLR — ablation and interaction evidence

**Chen et al., “A Simple Framework for Contrastive Learning of Visual Representations,” ICML 2020.**
[Proceedings paper](https://proceedings.mlr.press/v119/chen20j.html)

- Figure 2: separate augmentation, encoder, projection head and contrastive objective into a readable pipeline.
- Figure 5: a matrix is useful when the experimental design genuinely studies combinations of two factors.
- Figure 6: a diagnostic visualization can support a mechanism hypothesis, rather than merely repeat the headline metric.

Reusable pattern: method pipeline → factor interaction → mechanism diagnostic.

## 3. Mamba — algorithm, selection and systems context

**Gu and Dao, “Mamba: Linear-Time Sequence Modeling with Selective State Spaces,” COLM 2024.**
[arXiv paper](https://arxiv.org/abs/2312.00752)

- Figure 1: connect input-dependent selection with the hardware-aware scan.
- Figure 2: use a simple synthetic task to explain why selectivity matters before introducing the full state-space mathematics.
- Scaling and length-generalization figures should make the evaluation range and computational context explicit.

Reusable pattern: problem task → selective mechanism → systems-aware evidence.

## 4. DINO — qualitative evidence with quantitative checks

**Caron et al., “Emerging Properties in Self-Supervised Vision Transformers,” ICCV 2021.**
[Official CVF paper](https://openaccess.thecvf.com/content/ICCV2021/papers/Caron_Emerging_Properties_in_Self-Supervised_Vision_Transformers_ICCV_2021_paper.pdf)

- The attention visualizations are paired with quantitative comparisons.
- Thresholding choices and head-selection rules matter and should be stated.
- A qualitative map is not equivalent to a segmentation prediction or proof of semantic understanding.

Reusable pattern: input → model-derived visualization → explicit quantitative criterion → limitation.

## 5. Nature Communications — composite figure hierarchy

**“Accelerated land surface greening caused by earlier permafrost thawing,” Nature Communications (2025).**
[Article](https://www.nature.com/articles/s41467-025-67644-1)

Use this as a recent example for studying how multiple panels, maps, time-series results and explanatory labels are organized into a coherent journal figure. When borrowing a design idea, inspect the original caption, map scale, units, colorbar semantics and panel-specific data sources. Do not assume that a visual style can be transferred without its scientific context.

## How to use the atlas

For every paper figure selected for deeper study, record:
1. The scientific question answered by the figure.
2. The claim each panel supports.
3. The visual encoding and why it suits the data.
4. The experimental unit, baseline, uncertainty and normalization.
5. The caption details needed to interpret it correctly.
6. What could mislead a reader if the figure were copied without context.
7. A reusable pattern, not a copied artwork.
