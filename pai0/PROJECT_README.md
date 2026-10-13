# π₀ 复现项目导航

> 此页保留原本地项目的目录说明；GitHub 版只发布代码、配置和评测证据。论文 PDF、模型权重、离线安装包和已解压的视频副本不在仓库中。四套完整视频请下载 `reports/libero-runs/2026-09-29-official-50/` 下的归档。

这是 2024 年 π₀ 论文的学习与公开评测项目。当前完成的是**官方 `pi0_libero` 权重在 LIBERO 仿真中的评测**：40 项任务各 50 次，成功 1,845/2,000 次（92.25%）。官方训练代码和本项目的训练入口已准备并做静态检查，但本项目**没有执行 π₀ 预训练或 LIBERO 微调**，因此没有自训权重、训练曲线或训练成功率。论文的真实机器人实验与本项目的 LIBERO 仿真不是同一基准。

第一次打开此文件夹，建议按以下顺序阅读：

1. [项目结构与完整训练、运行流程](docs/PROJECT_GUIDE.md)：面向初学者，解释每个目录、主要脚本和实际运行顺序。
2. [复现与论文对照报告](reports/PI0_REPRODUCTION_AND_PAPER_COMPARISON.md)：讲清已完成部分、结果和与原论文的差异。
3. [正式评测报告](reports/libero-runs/2026-09-29-official-50/EVALUATION_REPORT.md)：四套成功率、40 项任务、原始日志和视频的入口。
4. [训练操作手册](docs/RUNBOOK.md)与[免训练评测手册](docs/NO_TRAIN_EVAL.md)：分别是两条操作路线，不要混用检查点来源。

## 目录一眼看懂

```text
Π0/
├─ input/                 论文原文
├─ config/                本地、云端、LoRA 三种实验配置
├─ scripts/               项目入口与辅助脚本；见 scripts/README.md
├─ tests/                 入口、结果解析和预算计算测试
├─ docs/                  教程、操作手册、方法与代码对照
├─ reports/               正式评测、早期试跑和复现报告；见 reports/README.md
├─ artifacts/offline/     离线源码与环境迁移归档
├─ examples/toy-flow/     独立教学小模型，不是 π₀ 训练
└─ .cleanup-backup/       可重建缓存的暂存备份，非实验结果
```

固定的官方 OpenPI 源码主要安装在原本地 WSL 的 `/home/xiao/pi0-reproduction/openpi`，并不直接展开在本目录。原本地项目曾有离线源码归档，GitHub 版未上传，可从[固定提交的官方源码](https://github.com/Physical-Intelligence/openpi/tree/215abfb217dbac7d5f1273282331b9b1866c0479)取得。官方已训练 `pi0_libero` 权重的本地副本原位于 `D:\xiao\pi0_download\pi0_libero`，不在本仓库中；本目录保留的是评测结果和来源记录。

在本机只做安全检查、不会启动训练：

```powershell
python -m pytest -q
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py status
```

`scripts/reproduce.py` 的阶段命令默认只打印计划；只有明确加 `--execute` 才可能下载、训练或评测。当前本机训练数据、归一化统计和自训检查点仍未就绪；云端正式评测所在实例已关机。不要把“脚本存在”理解为“训练已完成”。
