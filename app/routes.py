from flask import Blueprint, request, jsonify, render_template
from app.utils import process_upload, clinvar_query
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

@main.route('/results', methods=['GET'])
def results():
    task_id = request.args.get('task_id')
    if not task_id:
        return "缺少任务ID参数", 400

    task = tasks.get(task_id)
    if not task or 'result' not in task:
        return "任务ID无效或结果未生成", 404

    if task['status'] != 'completed':
        return "任务尚未完成，请稍后重试", 202

    variants = task['result'].get('variants', [])
    return render_template('results.html', variants=variants, task_id=task_id)


@main.route('/query_rsid', methods=['POST'])
def query_rsid():
    rsid = request.form.get('rsid')
    if not rsid:
        return jsonify({'error': '缺少 rsID 参数'}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        'status': 'queued',
        'progress': 0
    }

    thread = threading.Thread(target=process_rsid_background, args=(rsid, task_id))
    thread.start()

    return jsonify({'status': 'queued', 'task_id': task_id}), 202

# ----------------------------
# Background task processing
# ----------------------------

from app.utils.variant_utils import process_variants
import os
import traceback

def process_vcf_background(task_id, file_path, tasks):
    try:
        print(f"[INFO][{task_id}] 开始解析 VCF 文件: {file_path}")
        variants = process_upload.process_vcf(file_path)
        print(f"[INFO][{task_id}] VCF 文件解析完成，变异数: {len(variants)}")
        process_variants(task_id, variants, tasks, file_path)

    except Exception as e:
        print(f"[ERROR][{task_id}] 处理 VCF 时发生错误: {e}")
        traceback.print_exc()
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['progress'] = 100
        tasks[task_id]['error_message'] = str(e)


def process_rsid_background(task_id, rsid, tasks):
    try:
        print(f"[INFO][{task_id}] 开始处理 rsID : {rsid}")
        variants = process_upload.process_rsid(rsid)
        print(f"[INFO][{task_id}] rsID 转换为变异记录完成")

        process_variants(task_id, variants, tasks, file_path=None)

    except Exception as e:
        print(f"[ERROR][{task_id}] 处理 rsID 时发生错误: {e}")
        traceback.print_exc()
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['progress'] = 100
        tasks[task_id]['error_message'] = str(e)

