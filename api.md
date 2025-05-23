# API 接口文档

本项目为遗传变异注释与疾病风险预测系统，前后端通过以下 REST API 接口进行通信。

---

## 1. 上传VCF文件

**URL**：`/upload`
**Method**：`POST`
**请求体**：`form-data`

* `file`: VCF文件（单个样本）

**返回**：

```json
{
  "status": "success",
  "variants": [
    {"chrom": "chr1", "pos": 123456, "ref": "A", "alt": "T", "rsid": "rs123456"},
    ...
  ]
}
```

---

## 2. 查询变异注释信息（ClinVar）

**URL**：`/variant_info`
**Method**：`POST`
**请求体**（JSON）：

```json
{
  "rsid": "rs123456"
}
```

**返回**：

```json
{
  "rsid": "rs123456",
  "clinical_significance": "Pathogenic",
  "conditions": ["Breast cancer"],
  "review_status": "criteria provided, single submitter"
}
```

---

## 3. 氨基酸理化性质分析（Biopython）

**URL**：`/bio_features`
**Method**：`POST`
**请求体**（JSON）：

```json
{
  "before": "MVKVYAPASSANMSVGFDVLGAAVTPVDGALLGDVVTVEAAETFSLNNLGQK",
  "after": "MVKVYAPASSANMSVGFDVLGAAVTPVDGAFLGDVVTVEAAETFSLNNLGQK"
}
```

**返回**：

```json
{
  "molecular_weight_change": 18.02,
  "aromaticity_change": -0.0041,
  "instability_index_change": 1.25,
  "gravy_change": -0.12,
  "isolectric_point_change": 0.35
}
```

---

## 4. 查询RegulomeDB评分

**URL**：`/regulome_score`
**Method**：`POST`
**请求体**（JSON）：

```json
{
  "chrom": "chr1",
  "pos": 123456
}
```

**返回**：

```json
{
  "chrom": "chr1",
  "start": 123456,
  "end": 23456,
  "rsid": "rs123456",
  "ranking": 4,
  "probability_score": 0.85
}
```

---

## 5. 多基因风险评分预测（PRS）

**URL**：`/prs_predict`
**Method**：`POST`
**请求体**（JSON）：

```json
{
  "genotypes": {
    "rs123": "A/A",
    "rs456": "G/T",
    "rs789": "C/C"
  }
}
```

**返回**：

```json
{
  "prs_score": 3.72
}
```

---

如需联调测试，请确保本地服务器运行在 `http://localhost:5000/` 或服务器地址一致，并支持 CORS（跨域访问）。
