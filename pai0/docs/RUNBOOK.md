# π₀ 公开数据代理复现操作手册（训练暂不执行）

预算 100 元、希望**实际做 LoRA 训练**的独立路线见 [LOW_BUDGET_LORA.md](LOW_BUDGET_LORA.md)。下文仍描述原先的全参数微调方案；两条路线的检查点和结果不能混称。

如果决定跳过训练、直接评估已发布的官方 π₀-LIBERO 权重，请使用 [免训练评估手册](NO_TRAIN_EVAL.md)；不要把该权重当成本项目训练生成的 checkpoint。以下仍是原定的本地微调路线。

所有命令在 Windows PowerShell 的 `D:\xiao\Documents\ChatGPT\Π0` 下运行，除非另有说明。`scripts/reproduce.py` 在 WSL 中调用；不加 `--execute` 时仅打印命令，不下载数据或训练。阶段参数固定在 `config/experiment.json`。

## 0. 当前状态与代码核验

```powershell
.\scripts\verify.ps1
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py status
```

状态里的 `PENDING` 是未执行阶段，不代表前期环境损坏。`verify.ps1` 会再次跑轻量测试，约需数分钟。官方仓库应保持固定提交和干净状态。

训练配置的静态语义检查（不构造 3.3B 模型）：

```powershell
wsl -d openpi-ubuntu-22.04 -- bash -lc 'cd /home/xiao/pi0-reproduction/openpi && /home/xiao/.local/bin/uv run /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/check_config.py'
```

## 1. 数据与归一化（以后执行）

公开训练数据为 [physical-intelligence/libero](https://huggingface.co/datasets/physical-intelligence/libero)，与论文私有机器人训练数据不同。数据版本固定为 `a4336d589d589045d1c56423ffdf3b88a0e19b1f`；发布页标称 34.9 GB。当前 D 盘只有约 51.6 GB 空闲，因此下载入口要求至少约 69.8 GiB 可用空间，**本机当前会拒绝下载**。换到更大磁盘/云主机后先执行数据阶段，再计算统计：

```powershell
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py dataset
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py dataset --execute
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py norm
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py norm --execute
```

若使用外接盘或云主机的大磁盘，可先设置 `HF_LEROBOT_HOME` 环境变量，让下载与后续训练都使用相同的 LeRobot 数据根目录。官方 `compute_norm_stats.py` 会通过 LeRobot 读取数据并生成 `openpi/assets/pi0_libero/physical-intelligence/libero/norm_stats.json`。这一步可能需要大量网络流量、磁盘和时间，**本轮未执行**。完成后记录数据 commit、数据目录大小、`meta/info.json` 和 `norm_stats.json` 的 SHA-256。不要用数据集网页显示的样本数量代替已下载数据完整性校验。

## 2. 全量微调（以后在 >70 GB 显存机器上执行）

```powershell
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py train
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py train --execute
```

第二条命令会检查固定代码、数据元数据、归一化文件和显存；本机预计拒绝执行。数据元数据存在不等于完整下载，归一化必须对完整数据成功运行后再训练。它不会传 `--overwrite`，若实验目录已存在会拒绝覆盖。默认计划是 `pi0_libero`，30,000 步、seed 42、batch 32、W&B 关闭，并按官方建议设置 JAX 显存份额为 0.9。云主机上需把 `config/experiment.json` 中的 `openpi_repo`、`openpi_data_home`、`uv`、`base_checkpoint` 改成实际绝对路径，并将基础权重与数据快照复制过去。若不复制权重，官方配置会尝试从云端重新下载。训练期间保留完整命令、Git commit、数据哈希、日志、显卡型号、峰值显存及最终 checkpoint；只有损失曲线不等于策略成功率。

`pi0_libero_low_mem_finetune` 是另一条 LoRA 路线，官方最低要求仍 >22.5 GB；它不是此处 30k 全量微调的同一实验，不能只改配置名继续沿用结果标签。

## 3. 策略服务与 LIBERO 评测（训练后）

官方服务默认 LIBERO checkpoint 是 π₀.₅，**必须显式指定**本次 `pi0_libero` 的 checkpoint。训练保存的最后步号以实际目录为准，不假设是 30000。先查看：

```powershell
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py serve --checkpoint /path/to/openpi/checkpoints/pi0_libero/pi0_libero_public_proxy_v1/STEP
```

安装仿真环境时遵循固定提交的 `examples/libero/README.md`，使用其独立 Python 3.8 虚拟环境或 Docker 路线；当前只配置了训练用 Python 3.11，尚未安装 LIBERO 仿真依赖。本地已写好可执行的原生安装入口，默认只打印命令：

```powershell
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/setup_libero_sim.py
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/setup_libero_sim.py --execute
```

它按官方双 requirements 安装并生成 `config/libero-runtime/config.yaml`，避免 LIBERO 首次运行交互输入。安装后还需确认系统的 EGL/MuJoCo 图形库；官方 Dockerfile 给出了 Ubuntu 22.04 的依赖列表。Docker 路线须把 `SERVER_ARGS` 改为 `policy:checkpoint --policy.config pi0_libero --policy.dir ...`，不可使用默认 π₀.₅。若按原生路线建好 `examples/libero/.venv`，在一台 >8 GB 显存、支持 EGL 的机器上分别启动服务和四个 suite：

```powershell
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py serve --checkpoint /path/to/STEP --execute
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py eval --suite libero_spatial --execute
```

其余 suite：`libero_object`、`libero_goal`、`libero_10`。服务和评测分别在两个终端运行。评测时先确认服务端端口 8000 可达；若跨机器运行，官方客户端默认主机名需要通过其 CLI 参数设置。每个 suite 的日志写到 `reports/libero-logs/<suite>-<UTC>.log`，视频写到 `reports/libero-videos/<suite>/`。不要把视频数量当作试次数，因为官方脚本可能覆盖同名视频。

## 4. 结果验收（训练/评测后）

```powershell
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/summarize_libero.py --log libero_spatial=/path/to/spatial.log --log libero_object=/path/to/object.log --log libero_goal=/path/to/goal.log --log libero_10=/path/to/10.log --output /mnt/d/xiao/Documents/ChatGPT/Π0/reports/libero-results.json
```

解析器要求每套件 10 个任务、500 次试验，核对逐 episode 结果、任务成功率和最终成功率，才计算四套件宏平均。输出应与论文实验分开保存和命名。若有崩溃或不完整日志，先排查，不补填数字。
