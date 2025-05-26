import pandas as pd

_seen_prs_unmatched = set()

def compute_prs(variants):
    print(f"[INFO][compute_prs] 开始读取PRS数据文件...")
    prs_df = pd.read_csv("data/prs/pgs000001.csv")
    print(f"[INFO][compute_prs] 成功读取PRS数据文件，数据行数: {len(prs_df)}")

    print(f"[INFO][compute_prs] 开始清理数据，删除包含缺失值的行...")
    prs_df = prs_df.dropna(subset=['rsID', 'effect_allele', 'effect_weight'])
    print(f"[INFO][compute_prs] 清理完成后，数据行数: {len(prs_df)}")

    score = 0.0
    matched_snps = 0
    variant_dict = {v['id']: v for v in variants}
    print(f"[INFO][compute_prs] 变异信息已转换为字典，变异数量: {len(variant_dict)}")

    print(f"[INFO][compute_prs] 开始匹配PRS位点与变异信息...")
    for _, row in prs_df.iterrows():
        rsid = row['rsID']
        effect_allele = row['effect_allele']
        weight = row['effect_weight']
        print(f"[DEBUG][compute_prs] 正在处理 rsID = {rsid}, effect_allele = {effect_allele}, effect_weight = {weight}")

        if rsid in variant_dict:
            genotype = variant_dict[rsid]['genotype']
            dosage = genotype.count(effect_allele)
            score += dosage * weight
            matched_snps += 1
            print(f"[DEBUG][compute_prs] 匹配成功，变异 rsID = {rsid}, 剂型 = {genotype}, 剂量 = {dosage}, 得分 = {score}")
        else:
            if rsid not in _seen_prs_unmatched:
                print(f"[WARNING][compute_prs] 未找到 rsID = {rsid} 的变异信息，跳过")
                _seen_prs_unmatched.add(rsid)
            else:
                print(f"[DEBUG][compute_prs] rsID = {rsid} 的变异信息之前已跳过，继续跳过")

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


