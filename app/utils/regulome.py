import pandas as pd

reg_df = pd.read_csv('./data/regulome/regulome_data.csv')
_seen_reg_unmatched = set()

def query_score(position):
    try:
        chrom = position.get('chrom')
        start = position.get('start')
        end = position.get('end')
        key = f"{chrom}:{start}-{end}"

        print(f"[INFO][query_score] 开始查询位点 {key} 的 RegulomeDB 注释...")

        if None in (chrom, start, end):
            print(f"[WARNING][query_score] 输入字段不完整: {position}")
            return 'Invalid input'

        match = reg_df[
            (reg_df['chrom'] == chrom) &
            (reg_df['start'] == start) &
            (reg_df['end'] == end)
        ]

        if match.empty:
            if key not in _seen_reg_unmatched:
                print(f"[INFO][query_score] RegulomeDB 无匹配记录: {key}")
                _seen_reg_unmatched.add(key)
            else:
                print(f"[DEBUG][query_score] 位点 {key} 已查询过，仍未找到，跳过重复日志")
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
        print(f"[INFO][query_score] 成功找到 {key} 的 RegulomeDB 注释: {score_info}")
        return score_info

    except Exception as e:
        print(f"[ERROR][query_score] 查询失败: {e}")
        return 'Error'


