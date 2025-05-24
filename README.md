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

### 运行说明

* **项目目录结构要求**：`ensembl-vep` 文件夹必须位于项目根目录，与 `app/` 文件夹同级。
* 程序调用 VEP 时，会使用相对路径 `./ensembl-vep/vep` 来执行 VEP 脚本，无需你手动配置路径。


### 注意事项

* 请确保你已安装 Perl 及 VEP 依赖环境（具体请参照 VEP 官方文档）。
* 如果你需要将 `ensembl-vep` 放置在其他位置，请修改 `app/utils/vcf_parser.py` 中的 `run_vep` 函数，将 VEP 脚本路径改为对应绝对路径或通过环境变量传入。






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


