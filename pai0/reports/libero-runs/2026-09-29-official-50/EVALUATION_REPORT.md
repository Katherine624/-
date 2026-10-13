# π₀ 官方预训练权重：LIBERO 免训练评估报告

**状态：四套件完整评测，已通过本地一致性检查。**

本次直接使用官方发布的 `pi0_libero` 检查点（`gs://openpi-assets/checkpoints/pi0_libero`）进行仿真推理；**本项目没有训练或微调该模型**。这是公开 LIBERO 仿真基准评估，**不是**论文中私有机器人数据或真实机器人实验的复现。

## 总览

| 套件 | 成功 / 试验 | 成功率 | 逐次视频 |
|---|---:|---:|---:|
| libero_10 | 405 / 500 | 81.0% | 500 |
| libero_spatial | 486 / 500 | 97.2% | 500 |
| libero_object | 491 / 500 | 98.2% | 500 |
| libero_goal | 463 / 500 | 92.6% | 500 |
| 四套合计 | 1845 / 2000 | 92.25% | 2000 |

每个套件 10 项任务，每项 50 次试验；成功率按 `成功次数 ÷ 实际试验次数` 计算。本次各项样本量相同，合计成功率与已完成套件成功率的等权平均相同。

## 逐任务结果

| 套件 | 编号 | 任务（原始英文描述） | 成功 / 50 | 成功率 |
|---|---:|---|---:|---:|
| libero_10 | 00 | put both the alphabet soup and the tomato sauce in the basket | 43 / 50 | 86.0% |
| libero_10 | 01 | put both the cream cheese box and the butter in the basket | 49 / 50 | 98.0% |
| libero_10 | 02 | turn on the stove and put the moka pot on it | 36 / 50 | 72.0% |
| libero_10 | 03 | put the black bowl in the bottom drawer of the cabinet and close it | 49 / 50 | 98.0% |
| libero_10 | 04 | put the white mug on the left plate and put the yellow and white mug on the right plate | 43 / 50 | 86.0% |
| libero_10 | 05 | pick up the book and place it in the back compartment of the caddy | 46 / 50 | 92.0% |
| libero_10 | 06 | put the white mug on the plate and put the chocolate pudding to the right of the plate | 41 / 50 | 82.0% |
| libero_10 | 07 | put both the alphabet soup and the cream cheese box in the basket | 47 / 50 | 94.0% |
| libero_10 | 08 | put both moka pots on the stove | 9 / 50 | 18.0% |
| libero_10 | 09 | put the yellow and white mug in the microwave and close it | 42 / 50 | 84.0% |
| libero_spatial | 00 | pick up the black bowl between the plate and the ramekin and place it on the plate | 50 / 50 | 100.0% |
| libero_spatial | 01 | pick up the black bowl next to the ramekin and place it on the plate | 49 / 50 | 98.0% |
| libero_spatial | 02 | pick up the black bowl from table center and place it on the plate | 49 / 50 | 98.0% |
| libero_spatial | 03 | pick up the black bowl on the cookie box and place it on the plate | 50 / 50 | 100.0% |
| libero_spatial | 04 | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate | 45 / 50 | 90.0% |
| libero_spatial | 05 | pick up the black bowl on the ramekin and place it on the plate | 49 / 50 | 98.0% |
| libero_spatial | 06 | pick up the black bowl next to the cookie box and place it on the plate | 49 / 50 | 98.0% |
| libero_spatial | 07 | pick up the black bowl on the stove and place it on the plate | 50 / 50 | 100.0% |
| libero_spatial | 08 | pick up the black bowl next to the plate and place it on the plate | 49 / 50 | 98.0% |
| libero_spatial | 09 | pick up the black bowl on the wooden cabinet and place it on the plate | 46 / 50 | 92.0% |
| libero_object | 00 | pick up the alphabet soup and place it in the basket | 48 / 50 | 96.0% |
| libero_object | 01 | pick up the cream cheese and place it in the basket | 49 / 50 | 98.0% |
| libero_object | 02 | pick up the salad dressing and place it in the basket | 50 / 50 | 100.0% |
| libero_object | 03 | pick up the bbq sauce and place it in the basket | 48 / 50 | 96.0% |
| libero_object | 04 | pick up the ketchup and place it in the basket | 49 / 50 | 98.0% |
| libero_object | 05 | pick up the tomato sauce and place it in the basket | 50 / 50 | 100.0% |
| libero_object | 06 | pick up the butter and place it in the basket | 50 / 50 | 100.0% |
| libero_object | 07 | pick up the milk and place it in the basket | 48 / 50 | 96.0% |
| libero_object | 08 | pick up the chocolate pudding and place it in the basket | 50 / 50 | 100.0% |
| libero_object | 09 | pick up the orange juice and place it in the basket | 49 / 50 | 98.0% |
| libero_goal | 00 | open the middle drawer of the cabinet | 50 / 50 | 100.0% |
| libero_goal | 01 | put the bowl on the stove | 47 / 50 | 94.0% |
| libero_goal | 02 | put the wine bottle on top of the cabinet | 49 / 50 | 98.0% |
| libero_goal | 03 | open the top drawer and put the bowl inside | 39 / 50 | 78.0% |
| libero_goal | 04 | put the bowl on top of the cabinet | 50 / 50 | 100.0% |
| libero_goal | 05 | push the plate to the front of the stove | 47 / 50 | 94.0% |
| libero_goal | 06 | put the cream cheese in the bowl | 44 / 50 | 88.0% |
| libero_goal | 07 | turn on the stove | 50 / 50 | 100.0% |
| libero_goal | 08 | put the bowl on the plate | 49 / 50 | 98.0% |
| libero_goal | 09 | put the wine bottle on the rack | 38 / 50 | 76.0% |

## 原始证据与核验

- `libero_10`：[原始日志](libero_10/evaluation.log) · [逐任务 CSV](libero_10/task_results.csv) · [逐次 CSV](libero_10/episode_results.csv) · [机器结果 JSON](libero_10/summary.json) · [500 段视频](libero_10/videos) · [原始归档](libero_10.tar.gz)；归档 SHA-256 `556e96552682acfaa15b009bba0a4615bb731f6497d08d9346352a6ed029b1f0`。
- `libero_spatial`：[原始日志](libero_spatial/evaluation.log) · [逐任务 CSV](libero_spatial/task_results.csv) · [逐次 CSV](libero_spatial/episode_results.csv) · [机器结果 JSON](libero_spatial/summary.json) · [500 段视频](libero_spatial/videos) · [原始归档](libero_spatial.tar.gz)；归档 SHA-256 `0180fcfa3fd1e65259ea5e7f956f79c33e60a934582aa77f2fd604bdf127bbdf`。
- `libero_object`：[原始日志](libero_object/evaluation.log) · [逐任务 CSV](libero_object/task_results.csv) · [逐次 CSV](libero_object/episode_results.csv) · [机器结果 JSON](libero_object/summary.json) · [500 段视频](libero_object/videos) · [原始归档](libero_object.tar.gz)；归档 SHA-256 `e4ecf004dc44bbdccc5b3aee838eac99e2e2696bbeeb5e2f3a3c56a83e8259e2`。
- `libero_goal`：[原始日志](libero_goal/evaluation.log) · [逐任务 CSV](libero_goal/task_results.csv) · [逐次 CSV](libero_goal/episode_results.csv) · [机器结果 JSON](libero_goal/summary.json) · [500 段视频](libero_goal/videos) · [原始归档](libero_goal.tar.gz)；归档 SHA-256 `71a23ac600c63eb2ef6f0fff910ce40dc08db63895c4bebf6067963c93694928`。
- [运行清单](run-manifest.txt)。
- [逐套进度与退出状态](progress.tsv)。
- [四套汇总 JSON](summary.json)。
- [40 项任务 CSV](task_results.csv)。
- [2000 次试验 CSV](episode_results.csv)。
- [云端服务日志](reports/pi0-server-direct2-s7ryb4fgkw.log)。
- [评测运行脚本](scripts/run_official_libero_overnight.sh)。
- [逐次视频评测脚本](scripts/libero_eval_preserve_videos.py)。
- [原始元数据归档](run-metadata.tar.gz)。

核验范围：每套运行退出码为 0；原始日志含 500 条成败记录；JSON 内 10×50 次结果、CSV 行数、500 个非空 MP4 文件及文件名标记的成败互相一致；本地归档 SHA-256 与 `.sha256` 文件一致。这证明文件和计数的一致性，不等同于独立重做仿真。

## 警告与解释边界

- `libero_10` 日志中出现 `EGL_NOT_INITIALIZED` 2 次、Python traceback 2 次；该套运行退出码仍为 0 且 500 次结果齐全。需结合日志判断其发生在清理阶段，不能仅凭警告文字认定评估失败。
- `libero_spatial` 日志中出现 `EGL_NOT_INITIALIZED` 2 次、Python traceback 2 次；该套运行退出码仍为 0 且 500 次结果齐全。需结合日志判断其发生在清理阶段，不能仅凭警告文字认定评估失败。
- `libero_object` 日志中出现 `EGL_NOT_INITIALIZED` 2 次、Python traceback 2 次；该套运行退出码仍为 0 且 500 次结果齐全。需结合日志判断其发生在清理阶段，不能仅凭警告文字认定评估失败。
- `libero_goal` 日志中出现 `EGL_NOT_INITIALIZED` 2 次、Python traceback 2 次；该套运行退出码仍为 0 且 500 次结果齐全。需结合日志判断其发生在清理阶段，不能仅凭警告文字认定评估失败。
- 成功率来自 LIBERO 仿真器对 rollout 的成功判定；不是分类模型的验证集准确率，也不能推断真实机器人成功率。
- 这是单个模型检查点、单次配置与固定随机种子（运行脚本使用 seed 7）的结果；没有多种子重复、真实机器人外部验证或与论文所有训练条件的同条件对照。
- 本报告的数字由本地原始日志和视频重新核对。若需将结果写入论文，还应保存环境版本、检查点校验记录与运行命令，并说明与原文实验的差异。
