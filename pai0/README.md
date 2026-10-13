# π₀（pai0）复现记录

本目录保存 π₀ 项目的代码、配置、操作说明和已经完成的 LIBERO 仿真评测结果。

## 已完成与未完成

- **已完成**：下载 Physical Intelligence 发布的 `pi0_libero` 检查点，使用固定版本 OpenPI 在 LIBERO 四套任务上评测。每套 10 个任务，每任务 50 次；总计 **1845/2000 成功（92.25%）**，保存 2000 次逐次记录和 2000 段视频。
- **未完成**：本项目没有执行论文的大规模预训练，也没有运行从 `pi0_base` 到 `pi0_libero` 的微调；没有本项目自训权重，也没有论文中的真实机器人实验。这里的 92.25% 不能直接与原论文真实机器人指标比较。

详情见[正式评测报告](reports/libero-runs/2026-09-29-official-50/EVALUATION_REPORT.md)、[复现与论文对照](reports/PI0_REPRODUCTION_AND_PAPER_COMPARISON.md)和[项目状态](reports/REPRODUCTION_STATUS.md)。

## 文件怎么找

| 路径 | 内容 |
| --- | --- |
| `docs/` | 新手指南、论文到代码的对应关系、训练与评测操作说明 |
| `config/` | 公开 LIBERO 微调与评测配置；配置存在不代表训练已发生 |
| `scripts/`、`tests/` | 下载、检查、训练入口、评测汇总脚本及其测试 |
| `reports/libero-runs/2026-09-29-official-50/` | 正式评测报告、逐任务/逐次 CSV、原始日志、运行清单、视频归档与 SHA-256 |
| `reports/libero-runs/*-smoke/` | 独立的小规模链路试跑，不计入正式 2000 次结果 |

四个正式套件的 `.tar.gz` 是原始结果归档，内含逐次视频和日志；同目录的 `.sha256` 用于校验。GitHub 上没有再放一份解压后的 2000 个 MP4，以免重复占用空间。下载相应归档后可用 `tar -xzf 文件名.tar.gz` 解压。四套的成功数分别是：`libero_10` 405/500、`libero_spatial` 486/500、`libero_object` 491/500、`libero_goal` 463/500。

官方 OpenPI 源码固定提交为 `215abfb217dbac7d5f1273282331b9b1866c0479`；可从[官方仓库](https://github.com/Physical-Intelligence/openpi/tree/215abfb217dbac7d5f1273282331b9b1866c0479)取得。原论文可从[作者发布页](https://www.physicalintelligence.company/download/pi0.pdf)阅读。未上传模型权重、论文 PDF、安装缓存和可重新获取的离线源码包。
