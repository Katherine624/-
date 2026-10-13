# π₀ 本地存储与恢复说明

本仓库保存项目代码、配置、操作说明及已完成的 LIBERO 评测结果。它不是整台电脑的备份：模型权重、Python 安装缓存和 WSL 虚拟磁盘不在 Git 仓库内。清理本地文件前，应先区分可重新下载的依赖与不可替代的个人数据。

## 已在仓库中的内容

- `scripts/`、`config/`、`docs/`：复现代码、配置和操作说明。
- `reports/libero-runs/2026-09-29-official-50/`：四套正式评测的报告、日志、逐任务与逐次结果、各套视频归档及其 SHA-256 校验文件。该评测使用官方发布的 `pi0_libero` 权重，**没有进行本项目的模型训练**。

下载视频归档后，先用同目录的 `.sha256` 文件校验，再解压 `.tar.gz`。不要把只有代码和报告的仓库克隆误认为包含了 2000 段已解压视频或模型权重。

## 未上传的大文件

| 本地内容 | 用途与恢复方式 | 清理原则 |
| --- | --- | --- |
| `D:\xiao\pi0_download\pi0_libero` | 约 11.19 GiB 的官方模型检查点。上游地址为 `gs://openpi-assets/checkpoints/pi0_libero`；使用项目固定版本的 OpenPI 下载工具重新获取。 | 当前仍保留本地副本；仓库里只有来源说明，没有模型字节。 |
| `D:\xiao\pi0_env_transfer`、`D:\xiao\pi0_libero_transfer` | 约 22.44 GiB 的旧云端传输包、Linux Python 虚拟环境、`uv` 缓存和安装轮子。可按 `docs/RUNBOOK.md` 与项目配置重新安装。 | 属于可重建缓存，不是训练权重或评测结果；清理后再次离线部署需要重新准备。 |
| `D:\xiao\WSL\openpi-downloads` | 约 0.27 GiB 的 OpenPI/LIBERO 离线源码归档和部分下载文件。 | 可从上游重新取得。 |
| `D:\xiao\WSL\openpi-ubuntu-22.04\ext4.vhdx` | 约 31.24 GiB 的 π₀ 专用 WSL 系统盘。 | **未上传，也未删除**。它可能包含安装状态或尚未盘点的文件；不能把删掉它当作普通缓存清理。 |

GitHub 普通 Git 文件有 [100 MiB 单文件上限](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)，因此不能直接把上述多 GiB 文件加入 `pai0/`。Git LFS 有独立存储与带宽配额；启用或付费前需要单独决定。官方权重来自上游，不是本项目训练产物。

## 恢复顺序

1. 克隆本仓库，阅读 `pai0/README.md`、`pai0/docs/RUNBOOK.md` 与正式评测报告。
2. 按说明安装固定版本 OpenPI、Python 与 LIBERO 依赖。此前的本地传输缓存只为加快部署；删除后不会改变已经保存的评测结果。
3. 从官方 `gs://openpi-assets/checkpoints/pi0_libero` 下载检查点并校验完整性。不要把 `pi0_base` 或其他模型误当作本次评测权重。
4. 从正式评测目录下载所需套件的 `.tar.gz` 与 `.sha256`，校验后解压，即可检查逐次视频和原始日志。

`D:\xiao\Documents\ChatGPT\tao0`、`cosmos`、通用 `Ubuntu` WSL 系统盘等属于其他工作，不在本 π₀ 仓库的备份或清理范围内。
