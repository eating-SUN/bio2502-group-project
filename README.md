# 基因变异与蛋白质结构功能分析平台

本项目构建了一个基于 Flask 的 Web 应用，允许用户上传 VCF 文件，在本地自动完成变异注释、蛋白质氨基酸变化提取，并分析其对蛋白质结构和功能的潜在影响。


## 项目结构


## 前端开发（Vue3）

### 开发环境配置
1. 请确保已正确安装 `Node.js` 和 `npm`。
2. 在项目根目录下，导航至前端目录：
```bash
cd frontend
```
3. 安装项目依赖：
```bash
npm install
```
### 启动开发服务器
1. 在前端目录下运行以下命令启动开发服务器：
```bash
npm run dev
```
你可以在浏览器中访问给出的 URL 地址，查看应用。

2. 构建生产环境版本
在完成开发和测试后，可以在前端目录下运行以下命令构建生产环境版本：
```bash
npm run build
```
构建完成后的文件会输出到 frontend/dist 目录下，可将该目录下的文件部署到生产服务器。

## 安装 Ensembl VEP 工具

本项目依赖 [Ensembl Variant Effect Predictor (VEP)](https://www.ensembl.org/info/docs/tools/vep/index.html) 来注释基因变异的蛋白质影响。


### 安装方法

你可以运行以下脚本来自动下载并安装 VEP：

```bash
bash scripts/install_vep.sh
```

> 脚本会在项目根目录解压 `ensembl-vep` 文件夹，并完成基本配置。
> 缓存自动下载部分默认注释，避免重复下载。若需要，取消脚本中第 3 步缓存下载部分的注释即可自动安装缓存。


### 本地缓存与参考基因组配置

为了支持离线注释和 HGVS 格式输出，**你需要下载 VEP 缓存数据库和参考基因组 FASTA 文件**。
缓存数据库有两种获取方式，任选其一：

1. **自动安装缓存（推荐简单）**
   在 `scripts/install_vep.sh` 中取消注释第 3 步的缓存安装命令，执行脚本自动下载并安装缓存：

   ```bash
   perl INSTALL.pl --AUTO c --SPECIES homo_sapiens --ASSEMBLY GRCh38 --CACHEDIR ~/.vep
   ```

2. **手动下载缓存（灵活控制）**
   手动下载缓存文件并解压到缓存目录：

   ```bash
   curl -O ftp://ftp.ensembl.org/pub/release-114/variation/indexed_vep_cache/homo_sapiens_vep_114_GRCh38.tar.gz
   mkdir -p ~/.vep
   tar -xzf homo_sapiens_vep_114_GRCh38.tar.gz -C ~/.vep
   ```

   可用多线程下载工具 aria2 加速：

   ```bash
   aria2c -s 16 -x 16 "ftp://ftp.ensembl.org/pub/release-114/variation/indexed_vep_cache/homo_sapiens_vep_114_GRCh38.tar.gz"
   ```


### 参考基因组 FASTA 文件（用于 HGVS 表达式）

```bash
curl -O ftp://ftp.ensembl.org/pub/release-114/fasta/homo_sapiens/dna_index/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
mv Homo_sapiens.GRCh38.dna.primary_assembly.fa data/GRCh38/
```


### 其他说明

* 请确保你已安装 Perl 及 VEP 所需依赖（如 cpanm、gcc、make 等）。
* 如果将 `ensembl-vep` 文件夹或 `.vep` 缓存目录移动至其他位置，请更新程序中对应的路径配置。
* `.vep` 缓存目录默认是 `~/.vep`，若需更改，请在调用 VEP 时用 `--dir_cache` 参数指定。
* FASTA 文件路径通过 `--fasta` 参数传入，确保路径正确。



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

* 创建所需的目录结构（`data/clinvar`, `data/prs`, `data/regulome`）
* 下载：

  * ClinVar 数据文件（`variant_summary.csv`）
  * PRS 数据文件（`pgs000001.csv`, `pgs00000153.csv`, `pgs000212.csv`, `pgs000344.csv`, `pgs004153.csv`, `pgs005164.csv` 合并为的csv文件: `prs_breast_cancer.csv`）
  * RegulomeDB 数据文件（`regulome_data.csv`）

> 注意：该脚本使用了 `wget`，请确保你的系统已安装该工具，并保持网络连接。

## 项目贡献
* 欢迎对本项目进行贡献，你可以通过以下方式参与：
   * **提交问题**：如果你发现项目中存在 bug 或有功能改进建议，可以在 GitHub 仓库的 “Issues” 页面提交问题。
   * **提交代码**：你可以 Fork 本项目仓库，进行代码修改或功能开发后，通过 Pull Request 提交你的代码贡献。


