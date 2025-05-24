#!/bin/bash

# 安装 VEP 脚本

# 设置解压目录
VEP_DIR="ensembl-vep"

# 检查是否已解压
if [ -d "$VEP_DIR" ]; then
  echo "VEP 已经存在于 $VEP_DIR，不再重复解压。"
  exit 0
fi

# 解压 VEP 工具包
echo "正在解压 ensembl-vep.tar.gz..."
tar -xf ensembl-vep.tar.gz

# 检查解压是否成功
if [ -d "$VEP_DIR" ]; then
  echo "解压成功：$VEP_DIR"
else
  echo "解压失败，请检查 ensembl-vep.tar.gz 文件格式是否正确。"
  exit 1
fi

# 进入 VEP 目录并运行 INSTALL.pl 安装依赖
echo "正在初始化 VEP..."
cd $VEP_DIR
perl INSTALL.pl --AUTO ac --NO_TEST

echo "VEP 安装完成。"
