# π₀ LoRA：100 元封顶的真实训练试验

**状态：仅完成本地准备和静态检查；尚未租卡、下载训练集或运行 LoRA。**

本路线从官方 `pi0_base` 权重出发，用公开 `physical-intelligence/libero` 示范做真实 LoRA 参数更新，再用相同的 LIBERO 仿真协议评估。它是公开下游微调代理复现，不是原论文私有机器人数据预训练或真实机器人实验的严格复现。现有官方 `pi0_libero` 权重的 2,000 次结果保存在 `reports/libero-runs/2026-09-29-official-50/`，作为独立参照，绝不能重新命名为本次训练结果。

## 不可突破的预算边界

- 用户授权的是**所有新增租赁、数据盘及传输费用合计不超过 100 元**，而不是“训练费 100 元、评估另计”。
- 未看到新实例的实时单价、计费方式、余额、存储费和自动关机设置时，不启动收费实例。
- 首次试跑后**暂停**。记录实际账单、JAX 编译时间、稳定阶段每步耗时、峰值显存、训练日志和检查点；用 `scripts/estimate_lora_budget.py` 估算剩余训练、评估、结果回传与至少 15 元安全余量。估算不通过就不续训。
- 对任何收费实例，在平台控制台设定足够早的定时关机；代码中的步数限制和预算计算器都**不是计费硬上限**。优先传回检查点与日志，确认本地文件完整后关机并核对平台状态。
- 如果准备数据、启动环境或首次试跑就会使可用余额不足以回传成果，则不开始试跑。不要把之前截图中的小时价格当作当前价格。

## 当前机器与代码

- 本机 RTX 5060 Laptop 约 8 GiB 显存，不能按官方 π₀ LoRA 配置训练；D 盘剩余约 44 GiB，低于当前数据下载脚本的约 69.8 GiB 临时空间门槛。
- 固定 OpenPI 代码和 `pi0_base` 基础权重已在本机 WSL 就绪；公开 LIBERO 训练集、归一化统计量和本次 LoRA 检查点尚未就绪。
- 官方固定版本的 `pi0_libero_low_mem_finetune` 是 JAX LoRA 配置。官方文档估计训练需要超过 22.5 GB 显存，但实际显存依赖 batch、环境与版本；曾有 44 GB 的使用者报告。建议先核查 48 GB 及以上实例并短跑，仍不保证不 OOM。PyTorch 路线不作为本实验的 LoRA 入口。
- 新配置在 `config/experiment.lora.json`。它使用独立的训练目录 `pi0_libero_lora_budget100_v1`，不会覆盖过去的全量微调规划或官方免训练评估。

## A. 免费的本地检查

在 PowerShell 中：

```powershell
Set-Location 'D:\xiao\Documents\ChatGPT\Π0'
python -m unittest discover -s tests -v
wsl -d openpi-ubuntu-22.04 -- bash -lc 'cd /home/xiao/pi0-reproduction/openpi && PI0_EXPERIMENT_MANIFEST=/mnt/d/xiao/Documents/ChatGPT/Π0/config/experiment.lora.json /home/xiao/.local/bin/uv run /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/check_config.py'
wsl -d openpi-ubuntu-22.04 -- bash -lc 'PI0_EXPERIMENT_MANIFEST=/mnt/d/xiao/Documents/ChatGPT/Π0/config/experiment.lora.json python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py train --train-steps 100'
```

最后一行**不带 `--execute`**，只打印未来会运行的命令。不要在本机 8 GiB GPU 上尝试强行启动官方 LoRA。

## B. 新租实例就绪后，先核对再付费试跑

以下路径是说明，**不是可直接在未知新实例复制的命令**。把项目、固定 OpenPI 代码、基础权重放在新实例的大数据盘；将 `experiment.lora.json` 复制为该实例专用清单，并把 `openpi_repo`、`openpi_data_home`、`uv`、`openpi_venv`（如果使用）、`base_checkpoint` 改成真实绝对路径。设置足够大的 `HF_LEROBOT_HOME`，让数据和归一化训练过程读取同一份数据。数据集发布大小约 34.9 GB，另需缓存、临时下载、基础权重、训练检查点和结果空间；原先 50 GB 数据盘不够。

在新实例中固定 `PI0_EXPERIMENT_MANIFEST` 为专用清单路径后，顺序为：

```bash
python3 scripts/reproduce.py status
python3 scripts/reproduce.py dataset                 # 只看计划
python3 scripts/reproduce.py dataset --execute       # 真下载；先确认空间和价格
python3 scripts/reproduce.py norm --execute          # 真算本数据的归一化统计量
python3 scripts/reproduce.py train --train-steps 100  # 只看试跑计划
python3 scripts/reproduce.py train --train-steps 100 --execute
```

`100` 是**本次运行的目标总步数**，不是原论文或官方 30,000 步实验的完成度证明。若成功，检查 `checkpoints/pi0_libero_low_mem_finetune/pi0_libero_lora_budget100_v1/` 下是否出现数字命名的 step 检查点，并将它及 `reports/train-logs/` 回传本机。首轮如遇显存不足、数据不兼容、意外下载或损失异常，停止计费，先排查；不自动更换更贵实例。

## C. 试跑后计算能否继续

从平台读取实际已花费用与当前每小时单价；从试跑日志取**编译完成之后**的稳定秒/步。把预计评估、回传、关机所需小时数也算进去，例如：

```bash
python3 scripts/estimate_lora_budget.py \
  --budget-yuan 100 \
  --already-spent-yuan <平台实际新增消费> \
  --hourly-yuan <当前实际单价> \
  --seconds-per-step <实测稳定秒每步> \
  --current-step 100 \
  --target-step 30000 \
  --future-nontraining-hours <评估回传关机预计小时数> \
  --reserve-yuan 15
```

预算计算器只作估算，无法替代平台实时账单或定时关机。若 `fits_budget=False`，就把 100 步试跑诚实地交付为短程 LoRA 实验，或者选择预算内较小的目标步数；**不能称为完成官方 30,000 步微调**。若估算通过，也只分段续训，边跑边复核实际账单。续训同一实验使用 `--resume`，目标步数应逐渐增大，例如：

```bash
python3 scripts/reproduce.py train --train-steps 500 --resume       # 只看计划
python3 scripts/reproduce.py train --train-steps 500 --resume --execute
```

## D. 评估与交付

训练结束后记录实际 checkpoint 目录，启动该目录的 `serve`，再运行 `eval`；与官方权重评估使用相同套件、试次数、seed 和 `replan_steps`，但把新结果放在单独目录。先用少量试验检查策略能发动作、仿真能保存视频，再决定是否运行全部 2,000 次。新的成功率只有在相应试验实际完成、日志和视频计数核对后才能报告。

最终交付应至少包含训练清单、代码提交号、数据版本、实际训练步数、显卡与计费记录、损失日志、归一化统计量、自己的 LoRA 检查点、原始评估日志、逐任务和逐次结果、视频以及“和官方权重比较”的报告。若预算在评估前触顶，优先回传已有训练证据，报告为**训练完成但评估不完整**，不编造结果。
