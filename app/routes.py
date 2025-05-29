from flask import Blueprint, request, jsonify, render_template
from app.utils import process_upload, clinvar_query
import uuid
import threading
import os
import traceback
from flask import send_from_directory

main = Blueprint('main', __name__)

# save task status
tasks = {}


# 在 Flask 后端添加 API 路由
@main.route('/api/upload', methods=['POST'])
def upload_file_api():
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
        args=(task_id, file_path,tasks)
        )
    thread.start()

    return jsonify({'status': 'queued', 'task_id': task_id}), 202


@main.route('/api/status/<task_id>', methods=['GET'])
def get_task_status_api(task_id):
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


@main.route('/api/query_rsid', methods=['POST'])
def query_rsid_api():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    rsid = data.get('rsid')
    if not rsid:
        return jsonify({'error': '缺少 rsID 参数'}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        'status': 'queued',
        'progress': 0
    }

    thread = threading.Thread(target=process_rsid_background, args=(rsid, task_id,tasks))
    thread.start()

    return jsonify({'status': 'queued', 'task_id': task_id}), 202


@main.route('/api/results', methods=['GET'])
def get_results_api():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': '缺少任务ID参数'}), 400

    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': '任务ID无效'}), 404
    
    if task['status'] != 'completed':
        return jsonify({
            'task_status': task['status'],
            'progress': task.get('progress', 0),
            'message': '任务尚未完成'
        }), 202
    
    # 返回结构化结果
    return jsonify({
        'task_status': 'completed',
        'prsScore': task.get('result', {}).get('prs_score', 0),
        'prsRisk': task.get('result', {}).get('prs_risk', '未知'),
        'variants': task.get('result', {}).get('variants', [])
    })
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
        tasks[task_id]['progress'] = 20
        print(f"[INFO][{task_id}] VCF 文件解析完成，变异数: {len(variants)}")
        process_variants(task_id, variants, tasks, file_path)
        tasks[task_id]['progress'] = 100

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
        tasks[task_id]['progress'] = 10
        print(f"[INFO][{task_id}] rsID 转换为变异记录完成")

        process_variants(task_id, variants, tasks, file_path=None)
        tasks[task_id]['progress'] = 100

    except Exception as e:
        print(f"[ERROR][{task_id}] 处理 rsID 时发生错误: {e}")
        traceback.print_exc()
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['progress'] = 100
        tasks[task_id]['error_message'] = str(e)

# 在文件底部添加前端路由 fallback
@main.route('/', defaults={'path': ''})
@main.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')

# 添加静态文件路由
@main.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('../static', filename)

# 确保上传目录可访问
@main.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
