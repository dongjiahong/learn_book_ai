# Python 环境规则

在执行 Python 相关任务时，使用 conda 的 learn_book 环境。

## 具体规则：

- 激活环境：在运行 Python 命令前先激活 `learn_book` 环境
- Python 执行：使用 `conda activate learn_book` 后再执行 Python 脚本
- 包安装：在 learn_book 环境中安装 Python 包
- 虚拟环境：优先使用 conda 环境管理而不是 venv

## 命令示例：

```bash
# 激活环境
conda activate learn_book

# 运行 Python 脚本
conda activate learn_book && python script.py

# 安装包
conda activate learn_book && pip install package_name
# 或者使用 conda 安装
conda activate learn_book && conda install package_name

# 查看环境信息
conda activate learn_book && python --version
conda activate learn_book && pip list
```

## 注意事项：

- 所有 Python 相关的命令都应该在 learn_book 环境中执行
- 如果需要安装新的 Python 包，确保在正确的环境中安装
- 在提供 Python 命令建议时，总是包含环境激活步骤