# 基因变异与蛋白质结构功能分析平台

本项目构建了一个基于 Flask 的 Web 应用，允许用户上传 VCF 文件，在本地自动完成变异注释、蛋白质氨基酸变化提取，并分析其对蛋白质结构和功能的潜在影响。

## 项目结构



## 安装 Ensembl VEP 工具

本项目依赖 [Ensembl Variant Effect Predictor (VEP)](https://www.ensembl.org/info/docs/tools/vep/index.html) 来注释基因变异的蛋白质影响。

### 安装方法

我们已将 `ensembl-vep.tar.gz` 文件包含在项目根目录中。你可以运行以下脚本来自动解压和安装 VEP：

```bash
bash scripts/install_vep.sh
```

> 脚本会在项目根目录解压 `ensembl-vep` 文件夹，并完成基本配置。

### 本地缓存与参考基因组配置

为了支持离线注释和 HGVS 格式输出，**你还需要手动下载以下数据文件**：

1. **VEP 缓存数据库**（适用于 GRCh38）：

   ```bash
   curl -O ftp://ftp.ensembl.org/pub/release-114/variation/indexed_vep_cache/homo_sapiens_vep_114_GRCh38.tar.gz
   ```

   解压后将生成 `.vep` 缓存目录，可移动至项目根目录：

   ```bash
   mkdir -p ~/.vep
   tar -xzf homo_sapiens_vep_114_GRCh38.tar.gz -C ~/.vep
   ```
   * 注：可使用多线程下载工具加速下载，如aria2：

   ```bash
   # 安装 aria2（如未安装）
   # Ubuntu/Debian: sudo apt install aria2
   # macOS: brew install aria2

   # 使用 16 线程下载
   aria2c -s 16 -x 16 "ftp://ftp.ensembl.org/pub/release-114/variation/indexed_vep_cache/homo_sapiens_vep_114_GRCh38.tar.gz"
   ```
2. **参考基因组 FASTA 文件**（用于生成 HGVS 表达式）：

   ```bash
   curl -O ftp://ftp.ensembl.org/pub/release-114/fasta/homo_sapiens/dna_index/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
   gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
   mv Homo_sapiens.GRCh38.dna.primary_assembly.fa data/GRCh38/
   ```

   该命令会将解压后的 `.fa` 文件放在 `data/GRCh38/` 目录下。

### 运行说明

* **项目目录结构要求**：`ensembl-vep` 文件夹应位于项目根目录，与 `app/` 文件夹同级。
* 程序默认通过路径 `./ensembl-vep/vep` 调用 VEP 脚本。
* `.vep` 缓存目录默认为项目根目录下的 `.vep/`，如有更改请在 `run_vep()` 函数中修改 `--dir_cache` 参数。
* FASTA 文件路径通过 `--fasta` 参数传入，确保该路径正确指向解压后的 `.fa` 文件。

### 注意事项

* 请确保你已安装 Perl 及 VEP 所需依赖（详见 [VEP 官方文档](https://www.ensembl.org/info/docs/tools/vep/script/vep_download.html)）。
* 若将 `ensembl-vep` 文件夹或 `.vep` 缓存移动至其他位置，请相应更新 `app/utils/gene_to_protein.py` 中的路径设置。
* 建议将 `.vep/` 缓存目录和 `.fa` 文件加入 `.gitignore`，以避免上传至 Git 仓库。




## 下载数据文件

本项目依赖多个生物信息学数据库，包括：

* ClinVar：用于查询已知致病变异
* PRS（Polygenic Risk Score）数据：用于多基因风险评分
* RegulomeDB 数据：用于非编码区变异的功能注释

我们提供了一个自动下载脚本，能帮助你快速获取所需数据并放入正确的文件夹中。

### 下载方法

请在项目根目录运行以下命令：

```bash
bash scripts/download_data.sh
```

该脚本将自动完成以下操作：

* 创建所需的目录结构（`data/clinvar`, `data/dbNSFP5`, `data/prs`, `data/regulome`）
* 下载：

  * ClinVar 数据文件（`variant_summary.csv`）
  * PRS 数据文件（`pgs000001.csv`）
  * RegulomeDB 数据文件（`regulome_data.csv`）

> 注意：该脚本使用了 `wget`，请确保你的系统已安装该工具，并保持网络连接。


