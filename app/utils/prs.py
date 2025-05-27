import pandas as pd

_seen_prs_unmatched = set()

def compute_prs(variants, verbose=True):
    print(f"[INFO][compute_prs] 开始读取PRS数据文件...")
    prs_df = pd.read_csv("data/prs/pgs000001.csv")
    prs_df = prs_df.dropna(subset=['rsID', 'effect_allele', 'effect_weight'])
    print(f"[INFO][compute_prs] PRS清理完成, 保留有效行数: {len(prs_df)}")

    score = 0.0
    matched_snps = 0

    # 构建字典，统一 rsID 格式
    variant_dict = {}
    for v in variants:
        var_id = v['variant_info']['id']
        if var_id.startswith('rs'):
            var_id = var_id[2:]
        variant_dict[var_id] = v['variant_info']

    print(f"[INFO][compute_prs] 开始匹配PRS位点与样本变异...")
    for _, row in prs_df.iterrows():
        rsid = str(row['rsID']).lstrip('rs')
        effect_allele = row['effect_allele']
        weight = row['effect_weight']

        if rsid in variant_dict:
            genotype = variant_dict[rsid].get('genotype', '')
            if not genotype:
                if verbose:
                    print(f"[WARNING][compute_prs] 变异 rs{rsid} 缺失基因型信息")
                continue
            dosage = genotype.count(effect_allele)
            score += dosage * weight
            matched_snps += 1
            if verbose:
                print(f"[DEBUG][compute_prs] 匹配成功: rs{rsid}, 基因型 = {genotype}, 剂量 = {dosage}, 当前得分 = {score:.4f}")
        else:
            if rsid not in _seen_prs_unmatched:
                if verbose:
                    print(f"[WARNING][compute_prs] 未找到 rs{rsid} 的变异信息")
                _seen_prs_unmatched.add(rsid)

    print(f"[INFO][compute_prs] 共匹配到 {matched_snps} 个PRS位点，总得分为 {score:.4f}")
    return round(score, 4), matched_snps


def classify_risk(score, thresholds=[-1.0, 0.0, 1.0]):
    print(f"[INFO][classify_risk] 开始根据得分分类风险，阈值: {thresholds}")
    if score < thresholds[0]:
        print(f"[DEBUG][classify_risk] 得分 {score} 小于阈值 {thresholds[0]}, 分类为 低风险")
        return "低风险"
    elif score < thresholds[1]:
        print(f"[DEBUG][classify_risk] 得分 {score} 在阈值 {thresholds[0]} 和 {thresholds[1]} 之间, 分类为 中等风险")
        return "中等风险"
    elif score < thresholds[2]:
        print(f"[DEBUG][classify_risk] 得分 {score} 在阈值 {thresholds[1]} 和 {thresholds[2]} 之间, 分类为 高风险")
        return "高风险"
    else:
        print(f"[DEBUG][classify_risk] 得分 {score} 大于等于阈值 {thresholds[2]}, 分类为 极高风险")
        return "极高风险"


