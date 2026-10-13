# 合成数据的 flow matching 教学小模型

`train_toy_flow.py` 在 CPU 上用人工生成的数值数据训练一个小型 MLP，只用于观察“损失计算 → 参数更新 → 保存并重新加载检查点”的教学流程。它**不是 π₀，不使用 PaliGemma 或真实 LIBERO 示范，也不能产生论文/仿真成功率**。以前的独立运行保存在 `runs/20261009T053009Z/`，不进入 `reports/` 的正式结果。

查看参数但不开始新训练：

```powershell
wsl -d openpi-ubuntu-22.04 -- /home/xiao/pi0-reproduction/openpi/.venv/bin/python /mnt/d/xiao/Documents/ChatGPT/Π0/examples/toy-flow/train_toy_flow.py --help
```

上述命令使用已安装 PyTorch 的 WSL 环境；当前 Windows 默认 Python 没有 PyTorch，直接运行会提示缺少 `torch`。此教学脚本本身不需要 GPU，也不会调用云服务器。

若仅为学习而执行，它会在 `examples/toy-flow/runs/` 下生成明确标注为教学用途的损失 CSV、微型检查点和示例动作。完整 π₀ 训练的准备入口见[项目流程指南](../../docs/PROJECT_GUIDE.md)。
