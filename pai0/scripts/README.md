# 项目脚本索引

本目录的脚本负责组织官方 OpenPI 源码、保护训练入口、运行评测和核验结果；真正的 π₀ 模型、优化器及训练循环在固定版本的 OpenPI 仓库中。先看[项目流程指南](../docs/PROJECT_GUIDE.md)，再按下面的分工找代码。

| 类别 | 文件 | 作用 |
|---|---|---|
| 总入口 | `reproduce.py` | 读取 `config/experiment.json` 或指定清单，提供 `status/dataset/norm/train/serve/eval/serve-published/eval-published` 阶段；默认 dry-run，`--execute` 才执行 |
| 环境检查 | `openpi-shell.ps1`、`verify.ps1`、`verify_environment.sh` | 进入 WSL、核对固定代码/依赖/GPU、运行适合本机的官方基础测试 |
| 训练前准备 | `check_config.py` | 对照官方 `pi0_libero` 配置，不实例化完整模型；检查架构、动作长度、数据、步数等 |
| 训练前准备 | `download_dataset.py` | 下载固定版本的公开 LIBERO 示范数据；有磁盘空间与覆盖保护 |
| 可选预算路线 | `estimate_lora_budget.py` | 根据实测单步速度估算 LoRA 费用；不限制账单、不自动停机 |
| 权重获取 | `fetch_openpi_checkpoint.py` | 从官方 GCS 下载 `pi0_libero`，支持断点续传并校验大小与 MD5；所得不是自训权重 |
| 仿真环境 | `setup_libero_sim.py` | 准备独立 Python 3.8 LIBERO 环境；默认 dry-run |
| 正式评测 | `run_official_libero_overnight.sh` | 云端那次官方权重评测的四套顺序、截止时间、原始日志、视频与归档逻辑 |
| 正式评测 | `libero_eval_preserve_videos.py` | LIBERO 客户端改版：每次 rollout 单独存视频，不覆盖同名任务视频 |
| 结果核验 | `summarize_libero.py` | 解析原始日志，检查每任务次数和成功数，输出 JSON 与 CSV |
| 结果报告 | `render_official_libero_report.py` | 对照日志、CSV、视频、归档校验码生成中文评测报告 |

`run_official_libero_overnight.sh` 记录的是 **2026-09-29 那次云端运行**，包含当时的绝对路径和限时设置；不能直接当成新机器的通用启动脚本。一次新的租卡训练或评测应先复制、核对配置和目录，再进行 dry-run。单独的合成数据教学脚本在[示例目录](../examples/toy-flow/README.md)，不属于正式 π₀ 训练代码。
