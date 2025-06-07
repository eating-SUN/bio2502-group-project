# 基因变异与蛋白质结构功能分析平台

## 项目概述

本平台是一个集成了基因变异分析、蛋白质结构功能预测和临床意义评估的生物信息学分析系统。支持 VCF 文件上传、rsID 查询，结果可视化展示。主要功能包括：

- **变异注释**：通过Ensembl VEP工具对变异进行功能注释
- **蛋白质影响分析**：提取氨基酸变化并预测对蛋白质结构和功能的影响
- **临床意义评估**：整合ClinVar数据库和机器学习模型预测变异致病性
- **多基因风险评分(PRS)**：计算乳腺癌多基因风险评分
- **机器学习模型预测疾病风险**：使用机器学习模型预测乳腺癌患病风险
- **报告生成**：自动生成包含图表和详细分析结果的PDF报告

---

## 项目结构

```
.
├── run.py                       # 项目入口
├── to_csv.py                   # 工具脚本：VCF转CSV
├── requirements.txt            # Python依赖列表
├── README.md                   # 项目说明文档

├── app/                        # Flask 后端模块
│   ├── routes.py               # 路由定义
│   ├── pdf_report.py           # PDF 报告生成
│   ├── uploads/                # 上传的VCF文件
│   ├── static/                 # 前端静态资源
│   ├── templates/              # 前端 HTML 模板
│   └── utils/                  # 功能函数（如ClinVar查询等）

├── predict/                    # 疾病风险预测模块
│   ├── main.py                 # 预测主逻辑
│   └── model/                  # 训练好的模型文件

├── data/                       # 本地数据库和参考数据
│   ├── clinvar/               # ClinVar数据库（sqlite）
│   ├── regulome/              # RegulomeDB相关数据
│   ├── prs/                   # 多基因风险评分数据
│   └── GRCh38/                # 基因组参考文件

├── ensembl-vep/               # VEP工具（本地注释器）
│   └── ...                    # 由 Ensembl 提供的 VEP 文件

├── frontend/                  # Vue3 + Vite 前端项目
│   ├── src/                   # 前端源码
│   ├── public/                # 静态资源
│   └── package.json 等        # 前端配置文件

├── scripts/                   # 安装与数据下载脚本
│   ├── install_vep.sh         # 安装 VEP
│   ├── download_data.sh       # 下载 ClinVar、Regulome 数据
│   └── install_requirements.sh# 安装依赖

├── test_files/                # 示例 VCF 文件（用于测试）
├── node_modules/              # 前端依赖（自动生成）
└── user_manual/               # 用户手册

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

### 3. 安装前端开发服务器依赖（Vue3）

确保已安装 Node.js 和 npm（推荐 Node.js ≥ 16）：

```bash
cd frontend
npm install
```

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

---

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

---
## 运行项目

### 1. 启动后端服务

```bash
cd bio2502project
python run.py
```

### 2. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

### 3. 本地浏览器访问使用

点击前端终端中的链接或在浏览器访问显示的地址（如 [http://localhost:5173）](http://localhost:5173）)

---

## 测试数据演示
为了方便用户快速体验功能，项目内提供了测试数据：
 * test_files/test.vcf — 示例 VCF 文件
 * test_files/test_rsid.txt — 示例单个变异 rsID 列表

你可以在网页上上传该文件进行测试。

### 数据格式说明

#### VCF 文件格式

**必需字段：**

 - CHROM: 染色体编号
 - POS: 变异位置
 - ID: 变异标识符（如 rsID）
 - REF: 参考序列
 - ALT: 替换序列
 - QUAL: 变异质量
 - FILTER: 过滤条件
 - INFO: 附加信息

**示例：**
```
##fileformat=VCFv4.2
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chr1	10000	rs12345	A	T	100	PASS	AC=1;AF=0.5;AN=2;NS=1;DP=100;EAS_AF=0.5;AMR_AF=0.5;AFR_AF=0.5;EUR_AF=0.5;SAS_AF=0.5
```

#### rsID 列表格式

每行一个 rsID。
（网站仅支持单个rsID查询，列表仅供复制粘贴使用）

**示例：**
```
rs12345
rs67890
```

---

## 项目贡献
* 欢迎对本项目进行贡献，你可以通过以下方式参与：
   * **提交问题**：如果你发现项目中存在 bug 或有功能改进建议，可以在 GitHub 仓库的 “Issues” 页面提交问题。
   * **提交代码**：你可以 Fork 本项目仓库，进行代码修改或功能开发后，通过 Pull Request 提交你的代码贡献。

