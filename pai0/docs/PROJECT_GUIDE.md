# π₀ 项目结构与训练评测全流程指南

> GitHub 版是原本地项目的精简归档：论文 PDF、模型权重、离线安装包和解压后的 MP4 副本未上传；完整视频在同目录的四个评测 `.tar.gz` 中。下文的 WSL 和 D 盘路径是当时机器上的记录，不是新电脑的默认路径。

本指南帮第一次接触机器人模型的人辨认这个文件夹、读懂 π₀ 的训练和运行流程，并找到我们真实获得的结果。项目已完成官方权重的 LIBERO 仿真评测；本项目没有执行 π₀ 训练。先读本页，再去看具体脚本，比从几千行官方代码开始更容易。

## 一、先分清四种东西

| 名称 | 通俗理解 | 这个项目中的对应物 |
|---|---|---|
| 代码 | 做题的方法和程序 | 官方 OpenPI 固定提交、本目录 `scripts/` |
| 数据 | 教模型做题的示范 | 论文私有机器人数据不可用；公开 LIBERO 训练数据的下载入口已准备但未下载 |
| 权重/检查点 | 模型学习后保存的参数 | 官方发布的 `pi0_base` 与 `pi0_libero`；没有本项目训练出的检查点 |
| 评测结果 | 模型在新试验中的表现 | 四套 LIBERO 共 2,000 次 rollout 的日志、CSV、视频和 92.25% 成功率 |

**评测不会替代训练。** 评测时模型加载已有权重，根据仿真画面和任务指令输出动作；仿真器再判断成败。仅靠“模拟一遍训练流程”不可能产生等同于实际训练的 π₀ 权重。

## 二、文件夹和主要文件

```text
Π0/
├─ README.md                       从这里进入项目
├─ input/pi0-paper.pdf             用户提供的 2024 年 π₀ 论文
├─ config/
│  ├─ experiment.json              WSL 本地全参数微调计划，默认入口读取
│  ├─ experiment.cloud.json        云端路径版本；使用前必须核对实际路径
│  ├─ experiment.lora.json         单独的低显存 LoRA 计划，未运行
│  └─ reproduction.env             非机密环境设置记录
├─ scripts/                         本项目入口，详细作用见 scripts/README.md
├─ tests/                           本地单元测试
├─ docs/                            手册与方法说明
├─ reports/
│  ├─ PI0_REPRODUCTION_AND_PAPER_COMPARISON.md
│  └─ libero-runs/2026-09-29-official-50/  正式评测全部原始证据
├─ artifacts/offline/               离线安装/迁移归档，不是训练结果
└─ examples/toy-flow/               用合成数据教学的微型模型，不能并入 π₀ 指标
```

官方模型的核心实现不在本目录的 `scripts/` 中，而在[固定提交的 OpenPI 仓库](https://github.com/Physical-Intelligence/openpi/tree/215abfb217dbac7d5f1273282331b9b1866c0479)：`src/openpi/models/pi0.py` 定义损失与采样，`src/openpi/training/config.py` 定义 `pi0_libero` 训练参数，`scripts/compute_norm_stats.py` 计算数据统计，`scripts/train.py` 执行梯度更新，`scripts/serve_policy.py` 提供策略服务，`examples/libero/main.py` 是官方仿真客户端。本目录的 `scripts/reproduce.py` 负责把这些官方入口串起来、检查前置条件，并防止误触发付费步骤。原本地离线安装包未上传；论文与官方函数的更细对照见[方法对照](PAPER_TO_CODE.md)。

读代码时可按调用顺序看，而不必从仓库目录的第一页逐个打开：

| 官方 OpenPI 文件 | 在流程中的职责 | 新手应该关注什么 |
|---|---|---|
| `src/openpi/training/config.py` | 把模型、数据集、初始化权重、batch、步数等组合为训练配置 | 搜索 `pi0_libero`，先确认自己跑的是哪个配置 |
| `src/openpi/training/data_loader.py` | 从数据集取示范、组成 batch，送入图像/状态/动作变换 | 明白一个 batch 里有哪些输入和标准动作 |
| `src/openpi/models/pi0.py` | 定义网络、训练损失 `compute_loss` 与推理动作采样 | 区分训练时预测向量场和推理时生成动作块 |
| `src/openpi/training/optimizer.py` | 优化器及学习率相关设置 | 参数怎样随着梯度更新 |
| `src/openpi/training/checkpoints.py` | 保存、恢复参数与训练状态 | “模型权重”从哪里来，续训怎样接上 |
| `scripts/compute_norm_stats.py` | 先计算状态/动作的归一化统计 | 为什么训练、推理要使用同一尺度 |
| `scripts/train.py` | 把数据、模型、损失、优化器、检查点串成训练循环 | 真正发生训练的总入口 |
| `scripts/serve_policy.py`、`src/openpi/policies/libero_policy.py` | 加载权重并把原始观察转成模型输入，返回可执行动作 | 服务端怎样从检查点产生动作 |
| `examples/libero/main.py` | 创建 LIBERO 仿真、给策略发观察、执行动作并统计结果 | 成功率和逐次视频从哪里产生 |

这些文件都在 WSL 的 `/home/xiao/pi0-reproduction/openpi/` 下；本目录的 `scripts/README.md` 则解释我们自己的包装脚本。**不要把教学示例 `examples/toy-flow/` 当作上表的官方训练实现。**

## 三、论文中的模型怎样工作

一条训练示范可理解为“看到什么、接到什么指令、机器人目前怎样、接下来做了什么”：输入是多路 RGB 图像、自然语言任务和机器人自身状态；监督目标是一段未来连续动作。π₀ 以会理解图文的 PaliGemma 为基础，额外加入生成动作的 action expert。它不是从图像直接分类“成功/失败”，而是输出动作块；原始 π₀ 的默认动作块长度为 50。

训练时，程序把真实动作与随机噪声混合，令模型预测把中间动作沿所设概率路径变换的向量场，用 flow matching 的均方误差更新参数。每一步包括读取一个 batch、图像/文字/状态变换、计算损失、求梯度、优化器更新和按间隔保存检查点。训练损失下降只说明这个预测任务拟合得更好，**不能替代机器人成功率**。

推理时，模型收到当前图像、文字与状态，从噪声动作开始进行多步数值积分，得到连续动作块。控制程序只执行其中若干步，再取新观察重新调用模型。本次 LIBERO 评测每 5 步重新规划一次。论文方法见[作者发布的原始 PDF](https://www.physicalintelligence.company/download/pi0.pdf)第 III-V 节；公开实现的具体输入填充、动作归一化与采样方向以固定代码和[方法对照](PAPER_TO_CODE.md)为准。

## 四、训练全过程应该怎样走

这部分是**将来真正运行公开 LIBERO 微调时的操作路线**，不是本次已执行记录。原论文的机器人预训练涉及内部数据与约一万小时示范，本目录不能原样运行；这里准备的是官方 `pi0_libero` 公开下游微调：从官方 `pi0_base` 开始，在公开 LIBERO 数据上按配置训练 30,000 步。原论文提到的约 700,000 步预训练与这里的 30,000 步微调是两个不同阶段。

1. **固定版本与环境。** 确认 OpenPI Git 提交为 `215abfb217dbac7d5f1273282331b9b1866c0479`，Python/JAX 能识别 GPU，`pi0_base` 参数与配置相符。本地 `status` 和 `check_config.py` 可只读检查这些条件；租来的主机仍需重新检查路径与显存。
2. **下载训练示范。** `scripts/download_dataset.py` 从 `physical-intelligence/libero` 下载配置指定版本，并阻止覆盖已有数据。本项目的公开训练数据没有完整下载到当前训练目录。下载完应记录版本、文件数量和哈希，不能只凭网页显示的数据量说已就绪。
3. **算归一化统计。** 官方 `compute_norm_stats.py` 读取训练集状态/动作，生成 `norm_stats.json`。模型训练和推理必须使用匹配的数值尺度；只取得数据文件但缺统计，不能直接开始训练。
4. **初始化模型。** `pi0_libero` 配置选原始 π₀ 架构，从 `pi0_base` 加载基础参数，并指定 LIBERO 的图像、语言、状态和动作变换。固定版本公开配置为全参数微调、30,000 步、batch 32、seed 42、EMA 0.99；这些是计划参数，不是本项目实际跑出的训练记录。
5. **执行训练。** 官方 `scripts/train.py` 循环读取 batch，调用 `Pi0.compute_loss` 计算 flow matching 损失，反向传播并更新参数，按设置保存检查点。本项目 `scripts/reproduce.py train` 默认只展示命令；只有检查通过并显式给 `--execute` 才真正运行。需要另存日志、耗时、GPU 信息、数据版本、损失和最终检查点哈希，不能编造曲线。
6. **加载自训检查点做评测。** 如果将来确实得到新的检查点，再用 `reproduce.py serve --checkpoint <实际步号目录> --execute` 启动服务，并对同样的 LIBERO 四套按相同 seed、试验次数和重规划间隔测试，才可以与本次官方权重结果做同基准比较。

一次真正完成的训练，至少应留下：训练配置和代码提交号、数据版本、`norm_stats.json`、每步或定期记录的 loss、检查点目录、训练耗时与硬件信息。检查点是后续推理的输入；**训练 loss 不是仿真成功率**，需要另跑 rollout 才能得到后者。本项目目前没有这样的自训产物，只有前述官方权重评测证据。

当前本机 WSL 状态：固定代码、主 Python 环境、`pi0_base` 为 READY；训练数据元数据、归一化统计、自训检查点为 PENDING；本机显存约 7.96 GiB，不适合运行该全参数训练。训练脚本的静态配置检查通过，本地测试 22 项通过，但这些**不等于训练端到端成功**。云端曾配置好评测环境，现已关机。命令、磁盘与显存安全闸见[训练操作手册](RUNBOOK.md)。如果只想继续使用官方权重评测，训练数据和归一化步骤无需补做，走[免训练评测手册](NO_TRAIN_EVAL.md)。

## 五、这次已完成的运行过程

```text
官方发布 pi0_libero 权重
  → OpenPI 加载 params 和归一化 assets
  → 策略服务等待仿真请求
  → LIBERO 客户端生成图像、状态、语言指令
  → 模型返回动作块，客户端每 5 步重新规划
  → 仿真器判定每次成功/失败
  → 原始日志 + 逐次视频 + 归档
  → 解析成 40 任务 CSV、2,000 次 CSV、JSON 和中文报告
```

本次实际使用官方 `gs://openpi-assets/checkpoints/pi0_libero` 权重，OpenPI 固定版本，评测 seed 7。`libero_10`、`libero_spatial`、`libero_object`、`libero_goal` 各有 10 个任务，每任务 50 次，共 2,000 次。云端正式运行由 `scripts/run_official_libero_overnight.sh` 调用 `scripts/libero_eval_preserve_videos.py`，按套件保存 `evaluation.log` 和不覆盖的逐次 MP4；回传后由 `scripts/summarize_libero.py` 与 `scripts/render_official_libero_report.py` 核对记录、视频和归档哈希。正式结果为 405/500、486/500、491/500、463/500，合计 1,845/2,000（92.25%）。逐任务结果和所有证据见[正式评测报告](../reports/libero-runs/2026-09-29-official-50/EVALUATION_REPORT.md)。

别把这次评测误认为论文原实验：原论文主要在真实机器人上测折衣、整理餐桌等任务，使用允许部分完成分数的指标；本项目是 LIBERO 仿真二值成功率。完整对照与结论边界见[复现报告](../reports/PI0_REPRODUCTION_AND_PAPER_COMPARISON.md)。

## 六、最常用的安全检查命令

在 Windows PowerShell、此项目根目录执行：

```powershell
python -m pytest -q
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py status
wsl -d openpi-ubuntu-22.04 -- python3 /mnt/d/xiao/Documents/ChatGPT/Π0/scripts/reproduce.py train
```

最后一条**只是打印将来的训练命令，不会训练**。不要直接复制任何带 `--execute` 的命令去付费服务器，除非已核对数据、归一化、权重、路径、GPU、预算和停止机制。本目录未存储服务器密码。
