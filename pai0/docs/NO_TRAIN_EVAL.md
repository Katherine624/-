# 免训练评估：官方 π₀-LIBERO 权重

这条路线使用 Physical Intelligence 已发布的 `gs://openpi-assets/checkpoints/pi0_libero`，通过本项目固定版本的 OpenPI 在 LIBERO 四套件中重新运行仿真。它**不训练模型**，所得成功率是“使用官方已训练权重的独立评估”，不是“本项目训练所得结果”，也不是原论文私有真实机器人实验的复现。不要将别人的结果冒充成自己的训练结果。

2026-09-28 已直接核验官方公开 GCS 桶：此前缀下有 19 个对象，共 12,014,131,888 字节（11.19 GiB），含 `params/_METADATA` 和 `assets/physical-intelligence/libero/norm_stats.json`。官方仓库首页未列出该 π₀-LIBERO 权重，但这些对象确实可匿名读取。后续下载时应记录文件哈希和下载日期；GCS 路径本身不是不可变版本号。

## 需要的机器

- 模型服务：NVIDIA 显卡，显存**严格大于 8 GiB**；建议至少 16 GiB，留出 JAX 和图形运行余量。本机 RTX 5060 Laptop 只有 8151 MiB，未达到本项目的安全闸。
- LIBERO 客户端：可运行 MuJoCo/EGL，需独立 Python 3.8 环境和约 40 个任务的仿真资源。
- 磁盘：仅权重约 11.19 GiB，另需缓存、环境、日志和视频空间。训练数据和重新计算归一化统计**都不需要**。

## 在合适 GPU 主机上运行

先迁移本项目、固定提交的 OpenPI 仓库和 Python 环境，并在 `config/experiment.json` 中改好 `openpi_repo`、`openpi_data_home`、`uv` 等路径。下面命令中的 `/path/to/project` 换成实际项目根目录。先检查：

```bash
python3 /path/to/project/scripts/reproduce.py status
python3 /path/to/project/scripts/reproduce.py serve-published
python3 /path/to/project/scripts/reproduce.py eval-published --suite libero_spatial
```

首次准备仿真客户端（仅一次）：

```bash
python3 /path/to/project/scripts/setup_libero_sim.py --execute
```

在终端 1 启动官方 π₀ 权重服务。若云端没有权重，首次启动需下载约 11.19 GiB；当前云端路径已完成 19 个文件的官方大小与 MD5 校验：

```bash
python3 /path/to/project/scripts/reproduce.py serve-published --execute
```

确认服务加载完成且 8000 端口可达，再在终端 2 按顺序跑四套件：

```bash
python3 /path/to/project/scripts/reproduce.py eval-published --suite libero_spatial --execute
python3 /path/to/project/scripts/reproduce.py eval-published --suite libero_object --execute
python3 /path/to/project/scripts/reproduce.py eval-published --suite libero_goal --execute
python3 /path/to/project/scripts/reproduce.py eval-published --suite libero_10 --execute
```

`eval-published` 会提醒核对服务来源，因为客户端协议不能证明远端实际加载的是哪个模型。若服务和客户端分处两台机器，需要给客户端命令加 `--args.host <服务器地址>`；当前本项目入口未透传此参数，因此推荐两者先在同一主机上运行。日志文件名前缀为 `published-pi0-`，路径在 `reports/libero-logs/`。单套件预计 10 个任务 × 每任务 50 次试验；四套件共 2000 次。视频数量不可用于核对试验次数。

运行后从日志中取出四个实际路径，生成结果文件（不能预填数字）：

```bash
python3 /path/to/project/scripts/summarize_libero.py \
  --source official-published \
  --log libero_spatial=/path/to/spatial.log \
  --log libero_object=/path/to/object.log \
  --log libero_goal=/path/to/goal.log \
  --log libero_10=/path/to/10.log \
  --output /path/to/project/reports/pi0-published-libero-results.json
```

解析器核对逐试验成功/失败、任务率和总率；任何套件缺失或日志中断都不可写成已完成四套件评估。报告须注明：模型来源、OpenPI 提交、LIBERO 版本、评估种子、每任务试验数、replan_steps、硬件、成功率和未运行项。

官方仓库的 [LIBERO 文档](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/examples/libero/README.md)公布的 96.85% 平均成功率属于 **π₀.₅**，不能写成 π₀ 的结果。
