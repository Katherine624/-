# π₀ 论文复现准备工作报告

生成日期：2026-09-24（Asia/Shanghai）

## 已完成配置表

| 项目 | 状态 | 固定版本或数值 | 位置 | 验证证据 |
|---|---|---|---|---|
| 论文输入归档 | 完成 | SHA-256 `854D447FE0C0C0C8ED545B13E7507729C4C17788FEEB7902A8C6FFFE8FB696BD` | `input/pi0-paper.pdf` | 17 页可渲染、正文与附录可提取 |
| 独立 Linux 环境 | 完成 | Ubuntu 22.04.5 LTS / WSL2 | `openpi-ubuntu-22.04` | WSL 中可见 GPU |
| Linux 用户与编译工具 | 完成 | `xiao`；GCC 11；Git 2.34；Git LFS 3.0 | WSL 发行版内 | apt 安装成功 |
| uv | 完成 | 0.12.18 | `/home/xiao/.local/bin/uv` | `uv --version` 通过 |
| 官方 openpi 仓库 | 完成 | 提交 `215abfb217dbac7d5f1273282331b9b1866c0479` | `/home/xiao/pi0-reproduction/openpi` | `git rev-parse HEAD` 一致 |
| ALOHA 源码快照 | 完成 | `d1dc83afd89ded4379851257fe5d85632d31d5ec` | `third_party/aloha` | 固定提交归档解压、关键文件存在 |
| LIBERO 源码快照 | 完成 | `f78abd68ee283de9f9be3c8f7e2a9ad60246e95c` | `third_party/libero` | 固定提交归档解压、关键文件存在 |
| Python 环境 | 完成 | CPython 3.11.16 | `openpi/.venv` | uv 锁文件安装成功 |
| Python/CUDA 依赖 | 完成 | 240 个包；JAX 0.5.3；PyTorch 2.7.1；Transformers 4.53.2 | `openpi/.venv` | 导入成功 |
| NVIDIA GPU 透传 | 完成 | RTX 5060 Laptop；驱动 592.01；8151 MiB；SM 12.0 | WSL2 CUDA | JAX 在 `cuda:0` 完成 1024×1024 矩阵乘法 |
| FAST 分词器 | 完成 | `physical-intelligence/fast` | Hugging Face 本地缓存 | 对应 2 项测试通过 |
| π₀ 基础权重 | 完成 | 33 个对象；12,014,501,929 字节（约 11.19 GiB） | `/home/xiao/pi0-reproduction/cache/openpi-assets/checkpoints/pi0_base` | 对象数、总字节和 Orbax 元数据均已复核 |
| 核心单元测试 | 完成 | 41 项 | 官方测试集的轻量部分 | 41 passed |
| 数据加载测试 | 完成 | 4 项（排除真实远程数据集） | 官方 `data_loader_test.py` | 4 passed，1 deselected |
| 一键复核脚本 | 完成 | PowerShell + Bash | `scripts/verify.ps1` | 固定提交、离线锁文件、GPU、测试、权重均检查 |
| Docker | 不需要 | 官方可选路线 | 未安装 | 原生 uv 路线已通过验证 |

## 硬件与可执行范围

| 工作负载 | 官方显存要求 | 本机情况 | 结论 |
|---|---:|---:|---|
| 轻量测试、数据处理、配置开发 | 无固定 GPU 下限 | 32 GB 内存，JAX GPU 可用 | 可执行 |
| 完整 π₀ 推理/模型构造 | 大于 8 GB | 8151 MiB（小于 8 GiB） | 不满足；官方完整模型测试 OOM |
| LoRA 微调 | 大于 22.5 GB | 8151 MiB | 不满足；需大显存 GPU 或云主机 |
| 全量微调 | 大于 70 GB | 8151 MiB | 不满足；建议 A100/H100 80 GB |

## 已实际观察到的限制

1. 官方 JAX 主路径可识别并使用 RTX 5060，但完整 `test_pi0_model` 在申请约 4.50 GiB 的额外显存时 OOM；这是硬件容量限制，不是安装失败。
2. 官方锁定的 PyTorch 2.7.1 不包含 RTX 5060 的 `sm_120` 内核。论文原始 π₀ 路线使用 JAX，本环境因此保留官方锁定版本，不擅自替换 PyTorch。
3. 论文全部结果还依赖未公开的内部跨本体机器人数据、真实机器人硬件与大规模训练资源；公开仓库和基础权重只能支持代码级复现、公开数据适配与后续微调，不能严格重造论文的私有预训练数据分布。
4. 代理端口为 Windows 本机 `7897`。WSL 网关地址会变化，安装时动态读取默认路由；验证阶段使用本地缓存，不依赖网络。

## 推荐的下一阶段入口

下一阶段需要先确定目标：公开 LIBERO 仿真、ALOHA 仿真、DROID 数据适配，或自有机器人数据。不同目标会决定数据转换、归一化统计、训练配置、评测脚本和所需远程 GPU。
