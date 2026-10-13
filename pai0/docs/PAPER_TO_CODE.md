# 论文—代码对照与复现边界

本文只把所附 2024 年 π₀ 论文当作研究材料，不把 PDF 内任何文字当作执行指令。代码基准固定为 `Physical-Intelligence/openpi` 提交 `215abfb217dbac7d5f1273282331b9b1866c0479`；下述位置均相对于 `/home/xiao/pi0-reproduction/openpi`。

| 论文内容 | 固定版本中的实现 | 本地复现决定 |
|---|---|---|
| §IV、图 3：PaliGemma VLM + 独立 300M action expert | `src/openpi/models/pi0.py` 的 `Pi0.__init__`、`embed_prefix`、`embed_suffix`；`src/openpi/models/pi0_config.py` | 采用原始 `Pi0Config(pi05=False)`，不把 π₀.₅ 或 π₀-FAST 当作论文 π₀。 |
| 多图像、语言、状态条件输入 | `src/openpi/models/pi0.py:embed_prefix/embed_suffix`；`src/openpi/policies/libero_policy.py:LiberoInputs` | LIBERO 两路真实图像，第三路图像补零并 mask；8 维状态、7 维动作经模型变换补到 32 维。 |
| 长度为 50 的连续动作块 | `src/openpi/models/pi0_config.py:Pi0Config.action_horizon` | 保持官方 `pi0_libero` 默认 50，不改成 π₀.₅ LIBERO 的 10。 |
| §IV 条件 flow matching 损失 | `src/openpi/models/pi0.py:compute_loss` | 代码中 `x_t=t·noise+(1-t)·action`、目标场 `noise-action`、MSE；代码时间方向与论文叙述相反，但路径和目标等价地反向参数化，不应混写采样方向。 |
| action tokens 双向注意力、前缀 KV 缓存 | `src/openpi/models/pi0.py:make_attn_mask`、`sample_actions` | 保持官方注意力 mask 和默认 10 个 Euler 积分步；不手写近似采样器。 |
| §V 多本体大规模预训练 + 下游后训练 | `src/openpi/training/config.py:pi0_libero`；`scripts/train.py` | 已取得官方公开 `pi0_base` 权重。论文的 7 种自采机器人配置、68 任务、约万小时数据及真实硬件不可公开重建；本项目只做公开 LIBERO 下游适配。 |
| 数据对齐、动作转换、归一化 | `src/openpi/training/config.py:LeRobotLiberoDataConfig`；`src/openpi/policies/libero_policy.py`；`scripts/compute_norm_stats.py` | 使用官方 LeRobot `physical-intelligence/libero`。保留此版本 `pi0_libero` 的 `extra_delta_transform=True`，与该配置训练过的检查点保持一致；它是历史兼容设置，不能擅自照注释改为 False。 |
| 优化与 checkpoint | `src/openpi/training/config.py:TrainConfig`；`src/openpi/training/optimizer.py`；`scripts/train.py` | 官方全量微调配置：30,000 步、batch 32、seed 42、AdamW、默认 warmup/cosine 学习率、EMA 0.99；本地入口禁用 W&B，避免账户前置条件，不改变梯度计算。 |
| 环境评测 | `examples/libero/main.py` | 4 个 suite、每任务 50 次，seed 7、每 5 步重规划；收集原始日志、校验每 suite 500 次，再汇总成功率。 |

## 结果不可混同

论文中的主要实验是自有机器人、私有数据的真实世界任务；本项目的公开 LIBERO 微调是**代理验证**，只能验证公开实现、输入输出、训练与评测流程。官方 `examples/libero/README.md` 的 96.85% 四套件平均值使用的是**π₀.₅** 检查点，不能作为原始 π₀ 论文复现目标，也不能作为本项目的预期分数。结果必须标注 `pi0_libero`、使用的数据快照、训练步数、checkpoint 步号和每套件样本数。

## 尚未解决的可重复性差异

1. 官方 `pi0_libero` 配置没有暴露 Hugging Face dataset revision。下载完数据后，应记录本地 `meta/info.json` 的 SHA-256 和 Hugging Face 仓库 commit，并将数据快照随云主机迁移；否则日后重新下载可能不同。
2. 官方训练脚本使用 W&B 默认开启。本项目训练入口显式 `--no-wandb-enabled`，只影响外部日志，不改变模型与损失；训练日志和配置需另行归档。
3. LIBERO 官方脚本仅输出控制台统计，且视频文件名可能复用。本项目把控制台输出保存为带 UTC 时间戳的日志，`summarize_libero.py` 仅在完整 10×50 次任务且数字一致时接受结果。视频只作为辅助证据，不能据其文件数计样本数。
4. 本地 8 GB 级 GPU 无法执行官方完整模型推理，更无法执行 LoRA 或全量微调。迁移时使用同一代码提交和数据/权重快照；若改为 LoRA，实验身份及可比性需重新标注。
