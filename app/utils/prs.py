import pandas as pd

def compute_prs(variants, prs_file="data/prs/prs_breast_cancer.csv", verbose=True):

    # 1. 加载PRS数据
    try:
        prs_df = pd.read_csv(prs_file)
        required_cols = ['rsID', 'effect_allele', 'effect_weight']
        prs_df = prs_df.dropna(subset=required_cols)
        
        if verbose:
            print(f"[PRS] 加载 {len(prs_df)} 个乳腺癌风险位点 | 文件: {prs_file}")
            if 'risk_allele_freq' in prs_df.columns:
                print(f"[PRS] 检测到风险等位基因频率列")
    except Exception as e:
        raise RuntimeError(f"PRS文件加载失败: {e}")

    # 2. 预处理变异数据：将所有VCF中的变异按rsID存入字典
    var_dict = {
        v['variant_info']['id'].lstrip('rs'): v['variant_info']
        for v in variants 
        if 'id' in v['variant_info']
    }

    # 3. 初始化PRS得分、匹配计数器
    score = 0.0
    matched_snps = 0
    unmatched_snps = 0  # 新增：统计未匹配数量

    # 4. 遍历每个PRS权重位点进行匹配和计算
    for _, row in prs_df.iterrows():
        rsid = str(row['rsID']).lstrip('rs')
        effect_allele = str(row['effect_allele'])
        weight = float(row['effect_weight'])
        
        # 若VCF中无该rsID，记录未匹配数
        if rsid not in var_dict:
            unmatched_snps += 1
            continue
            
        # 解析基因型并计算剂量
        genotype = var_dict[rsid].get('genotype', '')
        dosage = genotype.count(effect_allele)
        
        # 若存在匹配剂量则累计得分
        if dosage > 0:
            score += dosage * weight
            matched_snps += 1
            if verbose:
                freq = row.get('risk_allele_freq', 'NA')
                print(f"[PRS] 匹配 rs{rsid}: 基因型={genotype} (剂量={dosage}) | "
                      f"权重={weight} 频率={freq} | 累计得分={score:.2f}")

    # 5. 打印最终统计信息
    final_score = round(score, 4)
    if verbose:
        print(f"[PRS] 最终得分: {final_score}")
        print(f"[PRS] 匹配位点数: {matched_snps} | 未匹配位点数: {unmatched_snps} | 总PRS位点: {len(prs_df)}")
    
    return final_score, matched_snps


def classify_risk(score, gender="female", verbose=True):

    # 女性乳腺癌阈值 
    thresholds = {
        'female': [0.5, 1.0, 1.5],  # 低/中/高/极高
        'male': [0.7, 1.2, 1.7]     # 男性乳腺癌较罕见
    }
    
    current_thresholds = thresholds.get(gender.lower(), thresholds['female'])
    
    if verbose:
        print(f"[PRS] 风险分类阈值: {current_thresholds} | 性别: {gender}")
    
    if score < current_thresholds[0]:
        risk = "低风险"
    elif score < current_thresholds[1]:
        risk = "中等风险"
    elif score < current_thresholds[2]:
        risk = "高风险"
    else:
        risk = "极高风险"
    
    if verbose:
        print(f"[PRS] 得分 {score:.2f} → 分类: {risk}")
    return risk