import sqlite3

def compute_prs(variants, prs_db="prs_brca.db", verbose=False):

    # 0. 从变异中提取rsID
    rsids = [v['variant_info']['id'] for v in variants if 'id' in v['variant_info']]

    if not rsids:
        print("[PRS] 输入变异列表为空或无rsID")
        return 0.0, 0
    
    # 1. 连接数据库查询PRS信息
    conn = sqlite3.connect(prs_db)
    placeholders = ",".join("?" for _ in rsids)
    query = f"SELECT rsID, effect_allele, effect_weight, source FROM prs WHERE rsID IN ({placeholders})"
    cursor = conn.execute(query, rsids)
    prs_data = cursor.fetchall()
    conn.close()

    # 转成字典
    prs_dict = {
        row[0]: {'effect_allele': row[1], 'effect_weight': float(row[2]), 'source': row[3]}
        for row in prs_data
    }

    # 2. 预处理变异数据：将所有VCF中的变异按rsID存入字典
    var_dict = {
        v['variant_info']['id'].lstrip('rs'): v['variant_info']
        for v in variants 
        if 'id' in v['variant_info']
    }

    # 3. 初始化PRS得分、匹配计数器
    score = 0.0
    matched_snps = 0
    unmatched_snps = 0  

    # 4. 遍历每个PRS权重位点进行匹配和计算
    for rsid in rsids:
        if rsid not in prs_dict:
            unmatched_snps += 1
            continue
        
        # 解析基因型并计算剂量
        effect_allele = prs_dict[rsid]['effect_allele']
        weight = prs_dict[rsid]['effect_weight']
        source = prs_dict[rsid].get('source', 'NA')

        genotype = var_dict.get(rsid, {}).get('genotype', '')
        dosage = genotype.count(effect_allele)
        
        # 若存在匹配剂量则累计得分
        if dosage > 0:
            score += dosage * weight
            matched_snps += 1
            if verbose:
                print(f"[PRS] 匹配 {rsid}: 基因型={genotype} (剂量={dosage}) | 权重={weight} 来源={source} | 累计得分={score:.2f}")

    # 5. 打印最终统计信息
    final_score = round(score, 4)
    print(f"[PRS] 最终得分: {final_score}")
    print(f"[PRS] 匹配位点数: {matched_snps} | 未匹配位点数: {unmatched_snps} | 总PRS位点: {len(rsids)}")
    
    return final_score, matched_snps


def classify_risk(score, gender="female", verbose=True):

    # 女性乳腺癌阈值 
    thresholds = {
        'female': [0.5, 1.0, 1.5],  # 低/中/高/极高
        'male': [0.7, 1.2, 1.7]     # 男性乳腺癌较罕见
    }
    
    current_thresholds = thresholds.get(gender.lower(), thresholds['female'])
    
    print(f"[PRS] 风险分类阈值: {current_thresholds} | 性别: {gender}")
    
    if score < current_thresholds[0]:
        risk = "低风险"
    elif score < current_thresholds[1]:
        risk = "中等风险"
    elif score < current_thresholds[2]:
        risk = "高风险"
    else:
        risk = "极高风险"
    

    print(f"[PRS] 得分 {score:.2f} → 分类: {risk}")
    return risk