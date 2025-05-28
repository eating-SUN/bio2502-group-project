from flask import Blueprint, request, jsonify, render_template
from app.utils import vcf_parser, variant_query, regulome, prs, bio_features
import uuid
import threading
import os
import traceback

main = Blueprint('main', __name__)

# save task status
tasks = {}

@main.route('/')
def index():
    return render_template('index.html')

# upload page
@main.route('/upload', methods=['GET'])
def upload_page():
    return render_template('upload.html')

@main.route('/results', methods=['GET'])
def results_page():
    task_id = request.args.get('task_id')
    
    # 统一响应格式
    base_data = {
        'task_status': 'pending',
        'prsScore': 0,
        'prsRisk': '未评估',
        'variants': []
    }

    if not task_id:
        base_data['task_status'] = 'invalid'
        return render_template('results.html', **base_data)

    task = tasks.get(task_id, {})
    status = task.get('status', 'invalid')
    base_data['task_status'] = status

    if status == 'completed':
        result = task.get('result', {})
        base_data.update({
            'prsScore': result.get('prs_score', 0),
            'prsRisk': result.get('prs_risk', '未知'),
            'variants': result.get('variants', [])
        })

    return render_template('results.html', **base_data)

# upload file
@main.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # generate unique task id
    task_id = str(uuid.uuid4())
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(UPLOAD_FOLDER, f'{task_id}.vcf')
    file.save(file_path)

    try:
        os.chmod(UPLOAD_FOLDER, 0o775)
    except:
        pass

    # start a task 
    tasks[task_id] = {
        'status': 'queued',
        'progress': 0,
        'file_path': file_path
    }

    # thread in background 
    thread = threading.Thread(
        target=process_vcf_background,
        args=(task_id, file_path)
        )
    thread.start()

    return jsonify({'status': 'queued', 'task_id': task_id}), 202


@main.route('/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    try:
        task = tasks.get(task_id)
        if not task:
            return jsonify({'error': 'Invalid task ID'}), 404

        if task['status'] == 'failed':
            return jsonify({
                'status': 'failed',
                'error_message': task.get('error_message', 'Unknown error')
            }), 500

        response = {
            'status': task['status'],
            'progress': task.get('progress', 0)
        }

        if task['status'] == 'completed':
            response['result'] = task.get('result')

        return jsonify(response)

    except Exception as e:
        print(f"[ERROR] 获取任务 {task_id} 状态失败：{e}")
        traceback.print_exc()  
        return jsonify({'error': '服务器内部错误，请查看终端日志'}), 500


# ----------------------------
# Background task processing
# ----------------------------

import os
import traceback

def process_vcf_background(task_id, file_path):
    try:
        print(f"[INFO] 任务 {task_id} 开始，处理文件：{file_path}")
        tasks[task_id]['status'] = 'parsing'
        tasks[task_id]['progress'] = 10

        # Step 1: 解析 VCF 文件
        try:
            print(f"[INFO][{task_id}] 解析 VCF 文件中...")
            variants = vcf_parser.process_vcf(file_path)
            print(f"[INFO][{task_id}] 解析完成，共获得变异 {len(variants)} 条")
            tasks[task_id]['progress'] = 30
        except Exception as e:
            raise RuntimeError(f"[{task_id}] VCF 文件解析失败: {e}")

        # Step 2: 查询 ClinVar 数据
        try:
            print(f"[INFO][{task_id}] 查询 ClinVar 数据中...")
            unmatched_count = 0
            for v in variants:
                if 'variant_info' in v:
                    clinvar_data = variant_query.query_clinvar(v['variant_info']['id'], quiet=True)
                    v['clinvar_data'] = clinvar_data
                    if clinvar_data.get('clinvar') is None:
                        unmatched_count += 1

            if unmatched_count == len(variants):
                print(f"[INFO][{task_id}] ClinVar 查询完成，但所有变异都未匹配上 ({unmatched_count}/{len(variants)})")
            elif unmatched_count > 0:
                print(f"[INFO][{task_id}] ClinVar 查询完成，有部分变异未匹配上 ({unmatched_count}/{len(variants)})")

            tasks[task_id]['progress'] = 40
        except Exception as e:
            print(f"[WARNING][{task_id}] ClinVar 查询失败: {e}")


        # Step 3: 计算蛋白理化性质
        try:
            print(f"[INFO][{task_id}] 计算蛋白理化性质中...")
            no_protein_info_count = 0
            for i, v in enumerate(variants):
                if 'protein_info' in v and v['protein_info']:
                    print(f"[DEBUG][{task_id}] 第 {i+1} 个变异涉及蛋白，开始计算理化性质")
                    pro_features = bio_features.calculate_protein_features(
                        v['protein_info']['wt_seq'],
                        v['protein_info']['mut_seq']
                    )
                    v['protein_features'] = pro_features
                else:
                    no_protein_info_count += 1

            if no_protein_info_count > 0:
                print(f"[DEBUG][{task_id}] {no_protein_info_count} 个变异无蛋白信息，跳过蛋白性质计算")

        except Exception as e:
            print(f"[WARNING][{task_id}] 蛋白性质计算失败: {e}")

        # Step 4: 查询 RegulomeDB 分数
        try:
            print(f"[INFO][{task_id}] 查询 RegulomeDB 分数中...")
            for v in variants:
                if 'clinvar_data' in v:
                    chrom = v['clinvar_data'].get('Chromosome')
                    start = v['clinvar_data'].get('Start')
                    end = v['clinvar_data'].get('Stop')
                    if chrom and start and end:
                        print(f"[DEBUG][{task_id}] 查询 RegulomeDB: {chrom}:{start}-{end}")
                        regulome_score = regulome.query_score({
                            'chrom': chrom,
                            'start': start,
                            'end': end
                        })
                        v['regulome_score'] = regulome_score
            tasks[task_id]['progress'] = 70
        except Exception as e:
            print(f"[WARNING][{task_id}] Regulome 分数查询失败: {e}")

        # Step 5: 计算 PRS
        try:
            print(f"[INFO][{task_id}] 计算 PRS 中...")
            prs_score, matched = prs.compute_prs(variants)
            prs_risk = prs.classify_risk(prs_score)
            tasks[task_id]['progress'] = 80
        except Exception as e:
            print(f"[WARNING][{task_id}] PRS 计算失败: {e}")
            prs_score = None
            prs_risk = None

        # Step 6: 保存结果
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
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[INFO] 已删除上传文件：{file_path}")
        except Exception as e:
            print(f"[WARNING] 删除文件失败: {file_path}，原因: {e}")
