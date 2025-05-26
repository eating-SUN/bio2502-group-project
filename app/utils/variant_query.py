import pandas as pd

clinvar_df = pd.read_csv("data/clinvar/variant_summary.csv", dtype=str)
clinvar_df['Chromosome'] = clinvar_df['Chromosome'].astype(str).str.strip()
clinvar_df['Start'] = clinvar_df['Start'].astype(str).str.strip()
clinvar_df['chrom_pos'] = 'chr' + clinvar_df['Chromosome'] + ':' + clinvar_df['Start']

_seen_clinvar_unmatched = set()
_seen_clinvar_matched = set()
_clinvar_unmatched_count = 0

def query_clinvar(variant_id):
    global _clinvar_unmatched_count

    def standardize_id(vid):
        if not isinstance(vid, str):
            return None
        if vid.startswith('rs'):
            return vid
        if ':' in vid and not vid.startswith('chr'):
            parts = vid.split(':')
            if len(parts) == 2:
                chrom, pos = parts
                return f'chr{chrom.strip()}:{pos.strip()}'
        return vid  # fallback

    try:
        variant_id_std = standardize_id(variant_id)
        if variant_id_std is None:
            raise ValueError("无法标准化 variant_id")

        # 判断匹配方式
        if variant_id_std.startswith('rs'):
            rsid_num = variant_id_std[2:]
            match = clinvar_df[clinvar_df['RS# (dbSNP)'] == rsid_num]
            match_type = 'rsID'
        elif ':' in variant_id_std:
            match = clinvar_df[clinvar_df['chrom_pos'] == variant_id_std]
            match_type = 'CHROM:POS'
        else:
            match = clinvar_df[clinvar_df['RS# (dbSNP)'] == variant_id_std]
            match_type = 'unknown'

        if match.empty:
            if variant_id not in _seen_clinvar_unmatched:
                _seen_clinvar_unmatched.add(variant_id)
                _clinvar_unmatched_count += 1
            return {'variant_id': variant_id, 'clinvar': None}

        if variant_id not in _seen_clinvar_matched:
            _seen_clinvar_matched.add(variant_id)

        return {'variant_id': variant_id, 'clinvar': match.iloc[0].to_dict()}

    except Exception as e:
        print(f"[ERROR][query_clinvar] 查询变异 {variant_id} 时出错: {e}")
        return {'variant_id': variant_id, 'clinvar': None}

