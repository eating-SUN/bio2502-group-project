#!/bin/bash
set -e

# VEP 版本（可以根据需要更改）
VEP_VERSION="release/114"  
VEP_DIR="ensembl-vep"

echo "开始安装 Ensembl VEP..."

# 1. 下载并解压 VEP
if [ ! -d "$VEP_DIR" ]; then
  echo "下载 VEP ${VEP_VERSION}..."
  curl -L -o ensembl-vep.tar.gz "https://github.com/Ensembl/ensembl-vep/archive/${VEP_VERSION}.tar.gz"
  tar -xzf ensembl-vep.tar.gz
  VEP_FOLDER=$(echo "$VEP_VERSION" | sed 's/\//-/g')
  mv "ensembl-vep-${VEP_FOLDER}" "$VEP_DIR"
  rm ensembl-vep.tar.gz
else
  echo "检测到已有 $VEP_DIR 文件夹，跳过下载"
fi

cd "$VEP_DIR"

# 2. 安装 Perl 依赖（需要有 cpanm 命令，若无需用户自行安装）
  #还可能需要安装gcc、make、DBI、DBD::mysql、htslib
echo "安装 Perl 依赖..."
#perl INSTALL.pl --AUTO c --NO_HTSLIB

# 3. 安装缓存（人类 GRCh38 版本）
echo "下载并安装缓存数据（homo_sapiens, GRCh38）..."
perl INSTALL.pl --AUTO c --SPECIES homo_sapiens --ASSEMBLY GRCh38 --CACHEDIR ~/.vep

echo "Ensembl VEP 安装完成！"

echo "请确保你的环境变量 PATH 包含 VEP 目录，例如："
echo "export PATH=\$PATH:$(pwd)"


