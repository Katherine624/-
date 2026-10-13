# LIBERO-Spatial 正式免训练评测

使用官方发布的 `pi0_libero` 权重，未进行任何训练。10 个任务各运行 50 次，共 500 次；成功 486 次，成功率 **97.2%**。这属于公开 LIBERO 代理实验，不是论文中的私有真实机器人实验。

- `evaluation.log`：原始运行日志；退出码为 0。
- `summary.json`：从日志复算并核验的机器可读结果。
- `task_results.csv`：10 个任务逐任务成功率。
- `episode_results.csv`：500 次 rollout 的逐次成败。
- `videos/`：500 段逐次视频。
- 上级目录 `libero_spatial.tar.gz`：云端原始归档，本地 SHA-256 `0180fcfa3fd1e65259ea5e7f956f79c33e60a934582aa77f2fd604bdf127bbdf` 与云端一致。

四套件均已完成；总体结论见上级目录的 [评估报告](../EVALUATION_REPORT.md)。
