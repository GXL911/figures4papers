# figures4papers Fork 审查与工程改造基线

日期：2026-11-16

## 仓库基线

- Fork：GXL911/figures4papers
- Upstream：ChenLiu-1996/figures4papers
- 基线提交：0ddfbd3fc9892e804a3fa01ae46bd0d32617f2aa
- Fork 和上游初始比对：identical；ahead=0；behind=0
- 文件树共 113 个条目；9 个研究项目目录；30 个 Python 文件（含一份 raw_data.py）；53 个图片文件。
- 本次审查包括全部 Python 文件的静态依赖与输出扫描，重点脚本的逻辑审查；并非全部旧脚本的端到端复现。

## 已发现的具体问题

| 优先级 | 文件 | 静态审查发现 | 处理策略 |
| --- | --- | --- | --- |
| P0 | figure_ophthal_review/plot_trend.py | 2023-02 重复键覆盖 Bard；2023-9 格式不一致；2025-08 超出时间轴 | 旧文件保留，迁移时独立修复 |
| P0 | figure_ImmunoStruct/raw_data.py | std 字段的部分元素除以 sqrt(5)，统计口径需要原始论文证据 | 不擅自更改原始数值 |
| P1 | figure_ophthal_review/plot_composition.py | 重复调用时直接修改全局 clinical_stage 标签 | 迁移时复制数据 |
| P1 | figure_VIGIL/plot_comparison_radar.py | 不同基准不同归一化尺度；NaN 用均值/零填充 | 保留示例，要求明确说明 |
| P1 | figure_Cflows/diffusion_swiss_roll.py | 随机生成未固定种子，索引查找存在重复遍历 | 添加确定性版本 |
| P2 | figure_VIGIL/plot_ablation.py | 右侧第二坐标轴重复绘制一条相同曲线 | 迁移时处理 |
| P2 | 多个旧脚本 | Latex/Helvetica、当前工作目录依赖、仅 PNG 导出 | 新增可移植 API |
| P2 | 原仓库整体 | 缺少统一可执行 API、测试与持续集成 | 本分支新增 |

## 本分支实际交付

- 可安装的 src/figures4papers Python 包。
- 字体与色彩风格、统计摘要、FigureContract、Figure Export、SHA256 Manifest。
- 数值、形状、误差含义、坐标轴和 Matplotlib Artist 检查。
- 四个明确标注 synthetic 的模板，输出 PNG/PDF/SVG。
- pytest 测试和 Python 3.10 / 3.12 GitHub Actions CI。
- Agent Skill 调用规范与完整脚本目录。

## 尚未完成的工作和边界

- 尚未逐个运行所有 29 个原始绘图脚本。
- 尚未证明旧 PNG 的像素级一致性，也未对所有源数据进行独立核验。
- 新模板属于合成数据教学示例，不是 PriceFM、Nano-Gym 或 About-Conv 实验结果。
- 即便数据检查通过，仍需人工检查期刊尺寸、文本冲突、色彩可访问性和科学解释。

## 后续迁移门槛

优先 ImmunoStruct -> MACL -> RNAGenScape；旧脚本、旧图片不覆盖。
每个迁移案例均应记录原始数据来源与统计意义，比较图中数值，
人工确认最终尺寸，并建立可重复运行的测试。
