import pandas as pd

# 读取 CSV 文件
clinvar_df = pd.read_csv("data/clinvar/clinvar.csv", dtype=str)
print(clinvar_df.columns)

# 兼容处理
clinvar_df.rename(columns={'CHROM': '#CHROM'}, inplace=True)

# 构建 chrom_pos 索引
if 'chrom_pos' not in clinvar_df.columns:
    clinvar_df['chrom_pos'] = clinvar_df['CHROM'].astype(str) + ':' + clinvar_df['POS'].astype(str)

# 构建 rsid 索引
if 'rsid' not in clinvar_df.columns:
    clinvar_df['rsid'] = clinvar_df['ID'].apply(lambda x: x if str(x).startswith('rs') else None)

def query_clinvar(variant_id):
    """
    支持三种查询方式：
    1. 直接匹配ID列 (如 3385321)
    2. 匹配rsID (如 rs121908936)
    3. 匹配染色体位置 (如 1:66926)
    """
    try:
        # 情况1：直接匹配ID
        if variant_id in clinvar_df['ID'].values:
            match = clinvar_df[clinvar_df['ID'] == variant_id]
        
        # 情况2：匹配rsID
        elif str(variant_id).startswith('rs'):
            match = clinvar_df[clinvar_df['rsid'] == variant_id]
        
        # 情况3：匹配染色体位置
        elif ':' in str(variant_id):
            chrom, pos = str(variant_id).split(':')
            match = clinvar_df[
                (clinvar_df['#CHROM'] == chrom) & 
                (clinvar_df['POS'] == pos)
            ]
        else:
            return {'variant_id': variant_id, 'clinvar': None}

        if match.empty:
            return {'variant_id': variant_id, 'clinvar': None}

        best_match = match.iloc[0].to_dict()
        return {
            'variant_id': variant_id,
            'clinvar': {
                'Chromosome': best_match['#CHROM'],
                'Start': best_match['POS'],
                'ID': best_match['ID'],
                'ClinicalSignificance': best_match.get('CLNSIG', 'Unknown'),
                'Gene': best_match.get('GENEINFO', 'Unknown').split('|')[0].split(':')[0],
                'Phenotype': best_match.get('CLNDN', 'Unknown'),
            }
        }

    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        return {'variant_id': variant_id, 'clinvar': None}


