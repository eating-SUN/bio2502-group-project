from app.utils import clinvar_query, bio_features, regulome, prs
import traceback
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
        tasks[task_id]['progress'] = 30

        # step2 : 计算RegulomeDB分数
        print(f"[INFO][{task_id}] 开始 RegulomeDB 注释")
        matched_count = 0
        unmatched_count = 0

        for v in variants:
            try:
                clinvar = v.get('clinvar_data')
                print(f"[DEBUG][{task_id}] 返回的ClinVar数据: {clinvar}")
                if clinvar:
                    rsid = clinvar.get('ID')
                    chrom = clinvar.get('Chromosome')
                    start = clinvar.get('Start')
                    end = clinvar.get('Stop')
                    print(f"[DEBUG][{task_id}] 待匹配位点: rsid={rsid}, chrom={chrom}, start={start}, end={end}")
                    pos_info = {}
                    if rsid and rsid != 'NA':
                        pos_info['rsid'] = rsid
                    if chrom and start and end:
                        pos_info.update({'chrom': chrom, 'start': start, 'end': end})
                    
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
        tasks[task_id]['progress'] = 40

        # step3: 计算蛋白质特征
        print(f"[INFO][{task_id}] 开始蛋白质理化性质计算")
        for v in variants:
            try:
                protein = v.get('protein_info')
                if protein and 'wt_seq' in protein and 'mut_seq' in protein:
                    print(f"[INFO][{task_id}] 计算蛋白质特征")
                    v['protein_features'] = bio_features.calculate_protein_features(
                        protein['wt_seq'], protein['mut_seq']
                    )
            except Exception as e:
                print(f"[WARNING][{task_id}] 蛋白质特征计算失败: {e}")
        tasks[task_id]['progress'] = 60

        # step4: 计算 PRS 风险评分
        prs_score = None
        prs_risk = None
        print(f"[INFO][{task_id}] 开始 PRS 风险评分计算")
        try:
            prs_score, matched = prs.compute_prs(variants)
            prs_risk = prs.classify_risk(prs_score)
            for v in variants:
                v['prs_score'] = prs_score
                v['prs_risk'] = prs_risk
            print(f"[INFO][{task_id}] PRS 计算完成，得分: {prs_score}，风险等级: {prs_risk}")
        except Exception as e:
            print(f"[WARNING][{task_id}] PRS 计算失败: {e}")
            for v in variants:
                v['prs_score'] = None
                v['prs_risk'] = None
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
                    'prs_score': prs_score,
                    'prs_risk': prs_risk,
                    'clinvar_data': [v.get('clinvar_data') for v in subset]
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
