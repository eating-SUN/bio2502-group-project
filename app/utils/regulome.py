import pandas as pd

reg_df = pd.read_csv('data/regulome/regulome_data.csv')
_seen_reg_unmatched = set()

def query_score(position):
    print(f"[INFO][query_score] 开始查询位点 {position} 的 RegulomeDB 分数...")
    chrom = position['chrom']
    start = position['start']
    end = position['end']

    match = reg_df[
        (reg_df['chrom'] == chrom) &
        (reg_df['start'] == start) &
        (reg_df['end'] == end)
    ]

    if match.empty:
        key = f"{chrom}:{start}-{end}"
        if key not in _seen_reg_unmatched:
            _seen_reg_unmatched.add(key)
        else:
            print(f"[DEBUG][query_score] 位点 {key} 的 RegulomeDB 注释之前已跳过，继续跳过")
        return 'Not Found'

    row = match.iloc[0]
    score_info = {
        'chrom': row['chrom'],
        'start': row['start'],
        'end': row['end'],
        'rsid': row['rsid'],
        'ranking': row['ranking'],
        'probability_score': row['probability_score'],
    }
    print(f"[INFO][query_score] 成功找到位点 {key} 的 RegulomeDB 注释，信息: {score_info}")
    return score_info

