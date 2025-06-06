# 基因变异与蛋白质结构功能分析平台

## 项目概述

本平台是一个集成了基因变异分析、蛋白质结构功能预测和临床意义评估的生物信息学分析系统。支持 VCF 文件上传、rsID 查询，结果可视化展示。主要功能包括：

- **变异注释**：通过Ensembl VEP工具对变异进行功能注释
- **蛋白质影响分析**：提取氨基酸变化并预测对蛋白质结构和功能的影响
- **临床意义评估**：整合ClinVar数据库和机器学习模型预测变异致病性
- **多基因风险评分(PRS)**：计算乳腺癌多基因风险评分
- **机器学习模型预测疾病风险**：使用机器学习模型预测乳腺癌患病风险
- **报告生成**：自动生成包含图表和详细分析结果的PDF报告


## 项目结构

```

```

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yxzhang-05/bio2502project.git
cd bio2502project
```

---

### 2. 安装 Python 后端依赖

建议使用 Python 3.8 及以上版本。

```bash
pip install -r requirements.txt
```

> 如使用虚拟环境：
>
> ```bash
> python -m venv venv
> source venv/bin/activate  # macOS/Linux
> venv\Scripts\activate     # Windows
> pip install -r requirements.txt
> ```

---

### 3. 启动前端开发服务器（Vue3）

确保已安装 Node.js 和 npm（推荐 Node.js ≥ 16）：

```bash
cd frontend
npm install
npm run dev
```

浏览器访问显示的地址（如 [http://localhost:5173）即可使用前端界面。](http://localhost:5173）即可使用前端界面。)

---

### 4. 安装 Ensembl VEP 注释工具

本项目依赖 [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) 注释基因变异的蛋白质影响。

#### 推荐：一键自动安装脚本

```bash
bash scripts/install_vep.sh
```

该脚本将：

* 下载 VEP 主程序到 `ensembl-vep/`
* 完成基础配置
* 默认 **不** 下载缓存和参考基因组（需手动执行）

---

## 缓存和参考基因组下载

如需使用 HGVS 表达式或支持离线注释，请按下列步骤下载附加资源。

### 1. 下载 VEP 缓存文件

```bash
mkdir -p ~/.vep
curl -O ftp://ftp.ensembl.org/pub/release-114/variation/indexed_vep_cache/homo_sapiens_vep_114_GRCh38.tar.gz
tar -xzf homo_sapiens_vep_114_GRCh38.tar.gz -C ~/.vep
```

（推荐）使用 aria2 加速下载：

```bash
aria2c -s 16 -x 16 "ftp://ftp.ensembl.org/pub/release-114/variation/indexed_vep_cache/homo_sapiens_vep_114_GRCh38.tar.gz"
```



### 2. 下载参考基因组 FASTA （GRCh38）

```bash
mkdir -p data/GRCh38
curl -O ftp://ftp.ensembl.org/pub/release-114/fasta/homo_sapiens/dna_index/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
mv Homo_sapiens.GRCh38.dna.primary_assembly.fa data/GRCh38/
```

> 请确保 VEP 主程序目录和缓存目录设置正确，可在 backend 或 config 中调整路径。


---

## 安装 Python 依赖

项目的所有 Python 依赖都整理在根目录的 `requirements.txt` 文件中。

你可以直接运行项目提供的安装脚本来自动创建虚拟环境并安装依赖：

```bash
bash scripts/install_requirements.sh
```

该脚本会完成以下操作：

* 创建并激活虚拟环境（默认名为 `venv`，在 `scripts/` 目录下）
* 使用 `requirements.txt` 文件安装所有依赖包


## 测试数据演示
为了方便用户快速体验功能，项目内提供了测试数据：
 * test_files/test_samples.vcf — 示例 VCF 文件
 * test_files/test_rsid.txt — 示例单个变异 rsID 列表

你可以在网页上上传该文件进行测试。


## 项目贡献
* 欢迎对本项目进行贡献，你可以通过以下方式参与：
   * **提交问题**：如果你发现项目中存在 bug 或有功能改进建议，可以在 GitHub 仓库的 “Issues” 页面提交问题。
   * **提交代码**：你可以 Fork 本项目仓库，进行代码修改或功能开发后，通过 Pull Request 提交你的代码贡献。
