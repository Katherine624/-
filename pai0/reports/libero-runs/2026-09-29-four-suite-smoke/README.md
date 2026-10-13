# π₀ 官方权重：LIBERO 四套件试跑结果

这是使用官方发布的 `pi0_libero` 权重做的**免训练**评测。每个套件的 10 个任务各运行 **1 次**，用于验证评测链路与估算耗时；不是论文原始机器人实验，也不是每任务 50 次的正式 LIBERO 评测。

| 套件 | 成功 / 次数 | 成功率 |
| --- | ---: | ---: |
| LIBERO-Spatial | 9 / 10 | 90% |
| LIBERO-Object | 9 / 10 | 90% |
| LIBERO-Goal | 9 / 10 | 90% |
| LIBERO-10 | 7 / 10 | 70% |
| 合计 | 34 / 40 | 85% |

可核对的原始资料在本目录：

- `summary.json`：从四份原始日志重新解析的机器可读汇总，明确标记 `small_sample_smoke_test`。
- `task_results.csv`：40 个任务的名称、成功/失败次数与成功率。
- `episode_results.csv`：40 次试跑逐次成功/失败记录。
- `libero-smoke-*.log`：逐任务、逐次成功/失败的原始运行日志。
- `libero-videos/smoke-*/`：40 段 rollout 视频，每个试跑 episode 一段。
- `smoke-four-suite-export.tar.gz`：云端原始结果的整体归档；本地 SHA-256 为 `d07ef5eab28894c2ca359485ff8dafc0465f5fca829f041c5de8c5da61577842`，与云端一致。

由于每任务仅 1 次，这里的成功率波动很大，不能据此断言正式性能。正式 50 次/任务评测另存于相邻目录，不会与试跑合并或冒充自训结果。
