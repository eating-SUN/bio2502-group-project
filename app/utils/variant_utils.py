from app.utils import clinvar_query, bio_features, regulome, prs
from app.utils.predict import predict_variant, compute_alt_dosage, load_model
import traceback
import torch
import os

def process_variants(task_id, variants, tasks, file_path=None):
    
    try:
        # step1: 注释 ClinVar
        print(f"[INFO][{task_id}] 开始 ClinVar 注释")
        success_count = 0
        fail_count = 0
        
        for v in variants:
            try:
                if 'variant_info' in v:
                    rsid = v['variant_info']['id']
                    result = clinvar_query.query_clinvar(rsid)
                    if result:
                        v['clinvar_data'] = result
                        success_count += 1
                    else:
                        fail_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                print(f"[WARNING][{task_id}] ClinVar 注释失败: {e}")
                fail_count += 1

        print(f"[INFO][{task_id}] ClinVar 注释完成，成功注释: {success_count} 条，未注释: {fail_count} 条")
        tasks[task_id]['progress'] = 20

        # step2 : 计算RegulomeDB分数
        print(f"[INFO][{task_id}] 开始 RegulomeDB 注释")
        matched_count = 0
        unmatched_count = 0

        for v in variants:
            try:
                clinvar = v.get('clinvar_data')
                if clinvar:
                    rsid = clinvar.get('ID')
                    chrom = clinvar.get('Chromosome')
                    pos = clinvar.get('Start')
                    pos_info = {}
                    if rsid and rsid != 'NA':
                        pos_info['rsid'] = rsid
                    if chrom and pos:
                        pos_info.update({'chrom': chrom, 'pos': pos})
                    
                    if pos_info:
                        score = regulome.query_score(pos_info)
                        v['regulome_score'] = score
                        if score != 'Not Found' and score != 'Invalid input' and score != 'Error':
                            matched_count += 1
                        else:
                            unmatched_count += 1
                    else:
                        unmatched_count += 1
                else:
                    unmatched_count += 1
            except Exception as e:
                print(f"[WARNING][{task_id}] RegulomeDB 注释失败: {e}")
                unmatched_count += 1

        print(f"[INFO][{task_id}] RegulomeDB 注释完成，匹配成功: {matched_count}，未匹配: {unmatched_count}")
        tasks[task_id]['progress'] = 30

        # step3: 计算蛋白质特征
        print(f"[INFO][{task_id}] 开始蛋白质理化性质计算")
        print(f"[DEBUG][{task_id}] variants 结构示例: {variants[0].keys()}")
        for idx, v in enumerate(variants):
            try:
                print(f"[DEBUG][{task_id}] 处理第 {idx+1} 个变异")
                protein = v.get('protein_info')
                if not protein:
                    print(f"[DEBUG][{task_id}] protein_info 不存在，跳过")
                    continue

                wt_seq = protein.get('wt_seq')
                mut_seq = protein.get('mut_seq')

                if not wt_seq or not mut_seq:
                    print(f"[DEBUG][{task_id}] 缺失 wt_seq 或 mut_seq，跳过")
                    continue

                print(f"[DEBUG][{task_id}] wt_seq 长度: {len(wt_seq)}, mut_seq 长度: {len(mut_seq)}")

                wt_seq_clean, wt_has_stop = bio_features.check_stop(wt_seq)
                mut_seq_clean, mut_has_stop = bio_features.check_stop(mut_seq)

                if wt_has_stop or mut_has_stop:
                    # 遇到提前终止，直接返回 None
                    v['protein_features'] = None
                    print(f"[WARNING][{task_id}] 第 {idx+1} 个变异检测到提前终止，跳过理化性质计算")
                else:
                    protein_features = bio_features.calculate_protein_features(wt_seq_clean, mut_seq_clean)
                    v['protein_features'] = protein_features
                    print(f"[INFO][{task_id}] 成功计算第 {idx+1} 个蛋白质特征")

            except Exception as e:
                print(f"[WARNING][{task_id}] 第 {idx+1} 个蛋白质特征计算失败: {e}")
                traceback.print_exc()

        tasks[task_id]['progress'] = 50

        # step4: 计算 PRS 风险评分
        prs_score = None
        prs_risk = None
        print(f"[INFO][{task_id}] 开始 PRS 风险评分计算")
        try:
            prs_score, matched = prs.compute_prs(variants)
            prs_risk = prs.classify_risk(prs_score)
            tasks[task_id]['prs_score'] = prs_score
            tasks[task_id]['prs_risk'] = prs_risk
            print(f"[INFO][{task_id}] PRS 计算完成，得分: {prs_score}，风险等级: {prs_risk}")
        except Exception as e:
            print(f"[WARNING][{task_id}] PRS 计算失败: {e}")
            tasks[task_id]['prs_score'] = None
            tasks[task_id]['prs_risk'] = None
        tasks[task_id]['progress'] = 60

        # step5: 模型预测
        try:
            model, gene_encoder = load_model()
            print(f"[INFO][{task_id}] 开始模型预测")

            total_score = 0.0
            total_dosage = 0.0
            score_list = []

            with torch.no_grad():
                for v in variants:
                    info = v.get("variant_info")
                    if not info:
                        continue

                    ref = info.get("ref")
                    alt = info.get("alt")
                    genotype = info.get("genotype", "NA")

                    if ',' in alt:
                        alt = alt.split(',')[0]

                    dosage = None
                    try:
                        dosage = compute_alt_dosage(ref, alt, genotype)
                    except Exception:
                        pass

                    score, clnsig_pred = predict_variant(model, gene_encoder, info)

                    # 记录模型预测结果到当前 v 中
                    v['predict_result'] = {
                        'predict_score': score,
                        'clnsig_pred': clnsig_pred,
                        }

                    score_list.append(score)

                    if dosage is not None and isinstance(dosage, (int, float)) and dosage > 0:
                        total_score += score * dosage
                        total_dosage += dosage

            if total_dosage > 0:
                final_score = total_score / total_dosage
            elif score_list:
                final_score = sum(score_list) / len(score_list)  # 或者用 final_score = score_list[-1]
            else:
                final_score = 0.0

            tasks[task_id]['score'] = final_score
            print(f"[INFO][{task_id}] 模型预测完成，总评分: {final_score:.4f}")

        except Exception as e:
            print(f"[ERROR][{task_id}] 处理变异失败: {e}")
            tasks[task_id]['error'] = str(e)
        
            tasks[task_id]['progress'] = 80

        # 保存结果
        try:
            print(f"[INFO][{task_id}] 整理结果中...")
            subset = variants[:100]
            tasks[task_id]['result'] = {
                'status': 'completed',
                'variants': subset,
                'summary': {
                    'variant_info': [v.get('variant_info') for v in subset],
                    'protein_info': [v.get('protein_info') for v in subset],
                    'protein_features': [v.get('protein_features') for v in subset],
                    'regulome_scores': [v.get('regulome_score') for v in subset],
                    'clinvar_data': [v.get('clinvar_data') for v in subset],
                    'predict_result': [v.get('predict_result') for v in subset]
                }
            }
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['progress'] = 100
            print(f"[INFO] 任务 {task_id} 完成 ✅")
        except Exception as e:
            raise RuntimeError(f"[{task_id}] 结果保存失败: {e}")

    except Exception as e:
        print(f"[ERROR] 任务 {task_id} 异常终止: {e}")
        traceback.print_exc()
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['progress'] = 100
        tasks[task_id]['error_message'] = str(e)

    finally:
        if file_path:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"[INFO] 已删除上传文件：{file_path}")
            except Exception as e:
                print(f"[WARNING] 删除文件失败: {file_path}，原因: {e}")
