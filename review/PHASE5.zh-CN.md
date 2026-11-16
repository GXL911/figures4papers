# Phase 5 — 原图复跑、图像回归和论文尺寸审查

本阶段把三件不同的事拆开验收：原绘图程序能否执行，重画后的图是否保留图表数据，以及缩到图稿尺寸后能否读清。原始基线为 `0ddfbd3fc989`，九个 `figure_*` 目录中的脚本、图和数组均不改动。

| 层级 | 证据 | 结论边界 |
|---|---|---|
| 原图复跑 | 29/29 脚本，45 份输出，含 42 PNG、3 PDF。同一便携环境两次独立执行，45 份输出的解码像素都相同 | PDF 比较的是 Poppler 栅格化像素，不要求含元数据的文件字节相同 |
| 与仓库旧图对照 | 44 个输出有同名参考。逐图记录像素尺寸、宽高比、RGB MAE、变化像素比例和并排图 | 对照用于发现差异，不要求不同字体、后端和源版本之间像素相同 |
| 回归基线 | CI 比较 45 个已复跑输出的图像签名和 PNG 版面诊断；丢图或超差会失败 | 基线针对本项目的便携渲染，不是实验数据基线，也不会发现所有微小视觉退化 |
| 论文尺寸 | 7 份新版图均导出 PNG、PDF、SVG 和 Manifest。对 PDF 复查实际宽度、可提取文字边界并以 180 DPI 渲染预览 | 178 mm 是本次验收设置，不是目标期刊承诺。SVG 的浏览器及字体环境可能不同 |
| 统计口径 | ImmunoStruct 四个原图面板对照期刊图注与脚本；MACL 验证同一数组的保留曲线；RNAGenScape 对照源数组 | 未取得并重新分析所有论文的逐次实验记录，不宣称独立复现实验结论 |

## 与旧图的差异如何解读

- `figure_CellSpliceNet/plot_ablation.py` 成功产生 `ablation.png`，但 Git 上没有同名原图。该图可检查重复渲染和今后的变化，不能称为与旧图匹配。
- `figure_RNAGenScape/plot_comparison.py` 与 `plot_comparison_speed.py` 默认输出同名的 `results_comparison_speed.png`，前者画 5 种方法，后者画 10 种。便携流程用脚本名隔离，保留两份图。唯一一张旧图不能作为两份不同图的等价证明。独立脚本相对同名旧图的宽高比变了约 11.11%，不是单纯抗锯齿差异。
- `figure_Cflows/diffusion_swiss_roll.py` 未设置种子，也没有在保存前建输出目录。执行器先创建输出目录，并从外部设种子 42。可重复的合成几何示意图不等于找回生成历史图片时的点云。
- 七个旧脚本依赖外部 LaTeX。便携模式在临时副本中换用 MathText，并对实际用到的少量 TeX 标签做显式映射。Helvetica 相关设置换为 DejaVu Sans。不要把外观差异默认归因于字体。对照图和量化差异保留在 CI 产物。
- 在 89/178 mm 指定宽度和 6 pt 阈值下，42 张原版 PNG 中有 26 张触发小字提示、6 张触发文字重叠候选、1 张触发画布越界候选。类别有重叠。密集的 MACL 学习子图和 RNAGenScape 原双热图是优先重排对象。这些是候选告警，不等于每一项都是真正的印刷缺陷。

## 七组新版图如何审查

| 案例 | 新图数 | 数据与设计决定 |
|---|---:|---|
| ImmunoStruct | 4 | 重画 IEDB 与 CEDAR 的比较／消融。用点和区间取代截断基线的条形，保留原图所绘行和区间端点，包括 CEDAR 消融的 `[6, 4, 0]`。图内按指标注明 SD/SEM |
| MACL | 1 | 在 3 个场景中重画 Sequential SFT、Replay、MACL 三种方法的平均保留曲线。第 `d` 个偏移只使用仍有观测的 `T-d` 项任务。脚本同时输出每个偏移的任务数；不把缩小的任务集合当同一批任务，也不从 Seed 1 推断区间 |
| RNAGenScape | 2 | 按原数组画 13 方法 × 6 方向的成功率与有符号中位变化。成功率用 0–100% 同一色标。符号变化图用以零居中的色标，颜色不等于优劣。去掉派生的相对改善行，不混同相对百分比与百分点 |

**ImmunoStruct 证据。** Nature Machine Intelligence 发表版的 Fig. 3a/b 和 Fig. 4a/b 图注说明，AUROC/AUPRC 区间为样本标准差，Mean PPVn 为标准误，图注报告五次独立实验。图注描述的五次重复也不自动等于完全相同的评估协议。原 `raw_data.py` 把第三列除以 `sqrt(5)` 后才入表。新版直接读取表示半宽的第三列，不再除一次。保留一个源码细节：CEDAR 对比行中的 ImmunoStruct Mean PPVn 是 0.364，消融行是 0.365。这里按各自源值保留，还没有逐次结果解释这一差异。来源：[论文 DOI](https://doi.org/10.1038/s42256-025-01163-y)，[发表版图注镜像](https://www.researchgate.net/publication/399264341_ImmunoStruct_enables_multimodal_deep_learning_for_immunogenicity_prediction?_fam=1)。

**MACL 口径。** 异构医疗任务面板等权混合 accuracy、ROUGE-L 和 micro-F1 在各自 0–100 尺度上的变化。它是描述性平均分，不是准确率。不同实验组计算排名时纳入的方法不同，不能把主对照与消融排名直接排序。

## 本地重跑与验收入口

建议用 Python 3.12，安装 [Poppler](https://poppler.freedesktop.org/) 的 `pdftoppm` 和 `pdftotext`。CI 中 Python 3.10 继续跑测试和最初的示例。只有 Python 3.12 跑完整图像回归。

```bash
python -m pip install -e ".[dev,legacy]" -c review/renderer-constraints.txt
python -m pytest -q
python tools/reproduce_legacy.py --repeat --baseline review/legacy-baseline.json
python examples/immunostruct_publication.py
python examples/macl_publication.py
python examples/rnagenscape_publication.py
python tools/review_publication_pdfs.py review/generated
```

- `legacy/report.json`。原脚本逐图 QA、SHA256 和已知变换。
- `legacy/diffs/`。原图、便携复跑图、放大差分，顺序从左到右。三列做同尺寸归一化以便差分，对应的像素尺寸和宽高比信息以报告为准。
- `legacy/publication-size/`。原布局按 89 或 178 mm 缩放的审查预览，不是新版修图结果。
- `publication-pdf-review/contact-sheet.png`。七张实际 PDF 的栅格预览。逐份审查用各自目录的大图。
- `macl/retention-cohorts.json`。三种方法在三个场景下每个偏移参与平均的任务数和对应结果。

图像回归签名是 48×32 的 RGB 区域均值加宽高比。阈值为归一化 MAE 0.012、明显变化格子比例 6%、宽高比变动 1.5%。小字计数允许一个字符项的跨渲染差异，越界和重叠候选数不允许增加。需要改基线时，先检查逐图差异，再显式用 `--write-baseline` 更新。生成文件不提交进历史 case 文件夹。

最终验收仍需要目标刊物的图稿尺寸、对应论文的原始运行记录和对适用版权条款的判断。目前不把原 29 个脚本标为可直接投稿，也不把新版显示视为新的研究结果。
