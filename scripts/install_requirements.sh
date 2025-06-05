#!/bin/bash

# 设置虚拟环境名称
ENV_NAME="venv"

echo ">>> 创建虚拟环境：$ENV_NAME"
python3 -m venv $ENV_NAME

# 激活虚拟环境（Linux/macOS 下）
source $ENV_NAME/bin/activate

echo ">>> 安装依赖包（来自 requirements.txt）"
pip install --upgrade pip
pip install -r ../requirements.txt

echo ">>> 所有依赖已安装完毕。"
echo ">>> 若使用的是 bash/zsh，可运行：source $ENV_NAME/bin/activate 进入虚拟环境"
