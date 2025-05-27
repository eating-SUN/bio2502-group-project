#!/bin/bash
set -e

# VEP版本
VEP_VERSION="release/114"
VEP_DIR="ensembl-vep"

echo "=== 开始安装 Ensembl VEP (${VEP_VERSION}) ==="

# 1. 下载并解压 VEP
if [ ! -d "$VEP_DIR" ]; then
  echo "未检测到目录 $VEP_DIR，开始下载 VEP 源码..."
  curl -L -o ensembl-vep.tar.gz "https://github.com/Ensembl/ensembl-vep/archive/${VEP_VERSION}.tar.gz"
  
  echo "解压缩 ensembl-vep.tar.gz ..."
  tar -xzf ensembl-vep.tar.gz
  
  VEP_FOLDER=$(echo "$VEP_VERSION" | sed 's/\//-/g')
  mv "ensembl-vep-${VEP_FOLDER}" "$VEP_DIR"
  rm ensembl-vep.tar.gz
  
  echo "VEP 下载并解压完成。"
else
  echo "检测到已有目录 $VEP_DIR，跳过下载。"
fi

cd "$VEP_DIR"

# 2. 安装 Perl 依赖（需要 cpanm 命令）
echo "安装 Perl 依赖（需要确保已安装 cpanm、gcc、make）..."
perl INSTALL.pl --AUTO c --NO_HTSLIB

# # 3. 安装缓存
# echo "下载并安装缓存数据（homo_sapiens，GRCh38）..."
# perl INSTALL.pl --AUTO c --SPECIES homo_sapiens --ASSEMBLY GRCh38 --CACHEDIR ~/.vep

echo "=== Ensembl VEP 安装完成 ==="
echo "请确保环境变量 PATH 包含 VEP 目录，例如："
echo "export PATH=\$PATH:$(pwd)"



