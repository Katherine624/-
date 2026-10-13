# π₀ 复现包状态

核对日期：2026-09-29。此表区分“文件已写好”“环境已验证”与“实验已完成”。

| 工作项 | 当前状态 | 本地位置或入口 | 后续条件 |
|---|---|---|---|
| 论文与官方代码 | 本地、云端均固定并验证同一 OpenPI 提交 | `input/pi0-paper.pdf`、`reports/PREPARATION_REPORT.md`；云端 `/root/autodl-tmp/openpi` | 保持提交 `215abfb217dbac7d5f1273282331b9b1866c0479` |
| 论文方法—代码对照 | 已写好 | `docs/PAPER_TO_CODE.md` | 无 |
| 公开代理实验配置 | 本地与云端配置已写好 | `config/experiment.json`、`config/experiment.cloud.json` | 云端使用独立 Python 3.11 环境 |
| 阶段入口与安全闸 | 已写好并通过 9 项本地测试；云端 dry run 正常 | `scripts/reproduce.py` | 显式 `--execute` 才运行 |
| 云端 OpenPI 主环境 | 已离线安装并验证 240 个锁定依赖；JAX 识别 GPU，模型加载、合成输入推理和 LIBERO 实际试跑均已验证 | `/root/autodl-tmp/openpi-venv311`、`/root/autodl-tmp/pi0-tools/uv` | 不能将合成输入推理当成任务成功率 |
| 公开 LIBERO 数据 | 固定版本下载脚本已写好，未下载 | `scripts/download_dataset.py`；版本 `a4336d5…` | 发布页 34.9 GB，D 盘仅余约 51.6 GB；需更大空闲空间 |
| 归一化统计 | 未生成 | `reproduce.py norm` | 先下载/读取完整数据 |
| π₀ 全量微调 | 未训练 | `reproduce.py train` | >70 GB 显存；数据和统计完成 |
| 训练 checkpoint | 未生成 | `openpi/checkpoints/pi0_libero/...` | 训练完成 |
| 官方 π₀-LIBERO 已微调权重 | 已下载至本机和云端；云端 19/19 文件与官方 GCS 大小、MD5 一致 | 本机 `D:\xiao\pi0_download\pi0_libero`；云端 `/root/autodl-tmp/openpi-assets/checkpoints/pi0_libero` | 此为官方已训练权重，非本项目训练成果 |
| LIBERO 仿真独立 Python 3.8 环境 | 已在云端离线安装官方 62 个锁定依赖；EGL 渲染、四套件试跑与正式评测通过 | `scripts/setup_libero_sim.py`、云端 `/root/autodl-tmp/libero-py38` | 云端实例已关机；重跑需重新开机 |
| 本地训练 checkpoint 的策略服务与四套件评测 | 未运行 | `reproduce.py serve/eval` | >8 GB 显存、训练 checkpoint、仿真环境 |
| 官方已训练 checkpoint 的免训练评测 | 四套件正式评测全部完成：40 项任务各 50 次，共 1845/2000 成功（92.25%）；云端实例已关机 | `reports/libero-runs/2026-09-29-official-50/EVALUATION_REPORT.md`；独立小样本见 `reports/libero-runs/2026-09-29-four-suite-smoke/` | 不得将官方预训练权重称作本项目训练成果 |
| 评测日志解析与验收 | 正式评测的四套日志、40 项任务 CSV、2000 次逐次 CSV、2000 段视频、原始归档及 SHA-256 已传回本机并核验 | `scripts/summarize_libero.py`、`scripts/render_official_libero_report.py`、`reports/libero-runs/2026-09-29-official-50/` | 如需报告论文原实验，仍缺私有预训练数据和真实机器人测试 |

当前不能声称“论文数值已复现”或“本项目完成训练”：论文私有预训练数据与真实机器人任务不开放；这里使用的是官方发布的 `pi0_libero` 已训练权重做公开 LIBERO 代理评测。此前的 40 次仅属独立链路试跑，不混入正式 2000 次结果。官方 LIBERO 文档公布的 π₀.₅ 数值不能与本项目的 π₀ 结果混用。
