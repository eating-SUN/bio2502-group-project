import pandas as pd

clinvar_df = pd.read_csv('data/clinvar/variant_summary.csv', dtype={'RS# (dbSNP)': str, 'Chromosome': str, 'Start': int, 'Stop': int})
# 生成一个用于pos查询的辅助列，比如 "7:4820844"
clinvar_df['chrom_pos'] = clinvar_df['Chromosome'] + ':' + clinvar_df['Start'].astype(str)

_seen_clinvar_unmatched = set()
_seen_clinvar_matched = set()
_clinvar_unmatched_count = 0

def query_clinvar(variant_id):
    global _clinvar_unmatched_count

    # 判断传入的是rsID还是chrom:pos格式
    if variant_id.startswith('rs'):
        # 去除rs前缀，保持数字字符串匹配
        rsid_num = variant_id[2:]
        match = clinvar_df[clinvar_df['RS# (dbSNP)'] == rsid_num]
    elif ':' in variant_id:
        match = clinvar_df[clinvar_df['chrom_pos'] == variant_id]
    else:
        # 可能直接是数字rsID字符串
        match = clinvar_df[clinvar_df['RS# (dbSNP)'] == variant_id]

    if match.empty:
        if variant_id not in _seen_clinvar_unmatched:
            _seen_clinvar_unmatched.add(variant_id)
            _clinvar_unmatched_count += 1
        return {'variant_id': variant_id, 'info': 'not found'}

    if variant_id not in _seen_clinvar_matched:
        print(f"[INFO][query_clinvar] 成功找到变异 {variant_id} 的 ClinVar 注释")
        _seen_clinvar_matched.add(variant_id)

    return match.iloc[0].to_dict()
