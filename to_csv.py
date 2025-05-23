import pandas as pd
import gzip

# 原始文件路径
input_path = 'data/PGS000001.txt.gz'
output_path = 'data/pgs000001.csv'

# 读取.gz文件
with gzip.open(input_path, 'rt') as f:
    # 跳过注释行（以#开头）
    lines = [line for line in f if not line.startswith('#') and line.strip()]

# 使用Pandas读取过滤后的内容
from io import StringIO
data = StringIO(''.join(lines))

# 自动识别分隔符为制表符
df = pd.read_csv(data, sep='\t')

# 打印列名以确认结构
print("列名：", df.columns.tolist())

# 提取关键列，或自动匹配
columns_needed = ['rsID', 'effect_allele', 'effect_weight']
missing = [col for col in columns_needed if col not in df.columns]

if not missing:
    df_filtered = df[columns_needed]
else:
    # 自动查找最相近的列名
    alt_columns = {
        'rsID': [col for col in df.columns if 'rs' in col.lower()],
        'effect_allele': [col for col in df.columns if 'allele' in col.lower()],
        'effect_weight': [col for col in df.columns if 'weight' in col.lower() or 'beta' in col.lower()]
    }
    rsid_col = alt_columns['rsID'][0]
    allele_col = alt_columns['effect_allele'][0]
    weight_col = alt_columns['effect_weight'][0]
    df_filtered = df[[rsid_col, allele_col, weight_col]]
    df_filtered.columns = ['rsID', 'effect_allele', 'effect_weight']

# 保存为 CSV
df_filtered.to_csv(output_path, index=False)
print(f"✅ 成功提取并保存到 {output_path}")