from flask import Blueprint, request, jsonify, render_template,send_file
from app.utils import process_upload
import app.pdf_report as pdf_report
import uuid
import threading
import os
import traceback
from fpdf import FPDF
import tempfile
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
    # 添加文件类型检查
    if not file.filename.lower().endswith('.vcf'):
        return jsonify({'error': 'Invalid file type'}), 400

    # 添加文件大小限制
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    file.seek(0, os.SEEK_END)
    if file.tell() > MAX_SIZE:
        return jsonify({'error': 'File too large'}), 400
    file.seek(0)
    
    # generate unique task id
    task_id = str(uuid.uuid4())
    global UPLOAD_FOLDER
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
            return jsonify({  # 移除500状态码
                'status': 'failed',
                'task_type': task.get('task_type', 'unknown') ,
                'error_message': task.get('error_message', 'Unknown error')
            })

        response = {
            'status': task['status'],
            'progress': task.get('progress', 0),
            'task_type': task.get('task_type', 'unknown') 
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

    # 修复：避免字典嵌套错误
    if isinstance(rsid, dict) and 'rsid' in rsid:
        rsid = rsid['rsid']

    if not rsid:
        return jsonify({'error': '缺少 rsID 参数'}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        'status': 'queued',
        'progress': 0
    }

    thread = threading.Thread(target=process_rsid_background, args=(task_id, rsid, tasks))
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
        'prsScore': task.get('result', {}).get('summary',{}).get('prs_score',0.0),
        'prsRisk': task.get('result', {}).get('summary',{}).get('prs_risk', '未知'),
        'modelScore': task.get('result', {}).get('summary',{}).get('model_score', 0.0),
        'modelRisk': task.get('result', {}).get('summary',{}).get('model_risk', '未知'),
        'variants': task.get('result', {}).get('variants', [])
    })



@main.route('/api/report', methods=['GET'])
def generate_report():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': 'Missing task_id'}), 400
    
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Invalid task_id'}), 404
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Task not completed'}), 400
    
    tmp_path = None
    try:
        # 生成PDF报告 - 设置自定义标题
        custom_title = "乳腺癌遗传风险分析报告"
        pdf = pdf_report.PDFReport(title=custom_title)  # 修复初始化参数
        
        # 添加封面标题
        pdf.set_title(custom_title)
        
        # 添加PRS信息
        result = task.get('result', {})
        pdf.add_section("PRS风险评分", [
            f"评分: {result.get('summary',{}).get('prs_score', 'N/A')}",
            f"风险等级: {result.get('summary',{}).get('prs_risk', '未评估')}",
            f"基于 {len(result.get('variants', []))} 个变异计算"
        ])
        
        # 添加神经网络预测信息
        model_score = result.get('summary',{}).get('model_score', 0.0)
        model_risk = result.get('summary',{}).get('model_risk', '未评估')
        pdf.add_section("神经网络预测风险评分", [
        f"评分: {model_score * 100:.2f}%",
        f"风险等级: {model_risk}"
        ])
        
        # 添加变异摘要
        variants = result.get('variants', [])
        
        # 安全地计算各种变异数量
        pathogenic_count = 0
        protein_affecting_count = 0
        regulome_scores = []
        
        for v in variants:
            clinvar_data = v.get('clinvar_data', {})
            # 检查是否存在ClinicalSignificance字段
            if clinvar_data and clinvar_data.get('ClinicalSignificance') == 'Pathogenic':
                pathogenic_count += 1
            
            if v.get('protein_info'):
                protein_affecting_count += 1
            
            regulome_score = v.get('regulome_score', {})
            if isinstance(regulome_score, dict) and 'ranking' in regulome_score:
                regulome_scores.append(regulome_score['ranking'][0])
        
        # 计算RegulomeDB分数分布
        regulome_distribution = {}
        for score in regulome_scores:
            regulome_distribution[score] = regulome_distribution.get(score, 0) + 1
        
        pdf.add_section("变异摘要", [
            f"总变异数: {len(variants)}",
            f"致病性变异: {pathogenic_count}",
            f"蛋白质影响变异: {protein_affecting_count}",
            f"高影响RegulomeDB分数 (1-2): {sum(count for score, count in regulome_distribution.items() if score in '12')}",
            f"中等影响RegulomeDB分数 (3-4): {sum(count for score, count in regulome_distribution.items() if score in '34')}",
            f"低影响RegulomeDB分数 (5-6): {sum(count for score, count in regulome_distribution.items() if score in '56')}"
        ])
        
        # 添加详细变异表格
        if variants:
            headers = ["变异ID", "染色体", "位置", "参考序列", "变异序列", "临床意义", "疾病名称", "RegulomeDB分数"]
            rows = []
            for v in variants[:15]:  # 只显示前15个
                var_info = v.get('variant_info', {})
                clinvar_data = v.get('clinvar_data', {})
                regulome_score = v.get('regulome_score', {})
                
                # 格式化RegulomeDB分数
                if isinstance(regulome_score, dict) and 'ranking' in regulome_score:
                    regulome_text = f"{regulome_score['ranking']} ({regulome_score.get('probability_score', 'N/A')})"
                else:
                    regulome_text = str(regulome_score)
                
                # 安全地获取各字段值
                rows.append([
                    var_info.get('id', ''),
                    var_info.get('chrom', ''),
                    str(var_info.get('pos', '')),
                    var_info.get('ref', ''),
                    var_info.get('alt', ''),
                    clinvar_data.get('ClinicalSignificance', '未知'),
                    clinvar_data.get('ClinvarDiseaseName', '-'),
                    regulome_text
                ])
            pdf.add_table("变异列表 (前15个)", headers, rows)
        
        # 添加蛋白质变异信息
        protein_variants = [v for v in variants if v.get('protein_info')]
        if protein_variants:
            pdf.add_section("蛋白质变异信息", [f"共发现 {len(protein_variants)} 个影响蛋白质功能的变异"])
            # 只展示前3个蛋白质变异
            for idx, variant in enumerate(protein_variants[:3]):
                protein_info = variant.get('protein_info', {})
                # 确保有足够的序列信息
                if 'wt_seq' not in protein_info:
                    protein_info['wt_seq'] = "无野生型序列数据"
                if 'mut_seq' not in protein_info:
                    protein_info['mut_seq'] = "无突变型序列数据"
                
                pdf.add_protein_section(f"蛋白质变异 #{idx+1}", protein_info)
        
        # 添加图表 - 使用try-except确保即使图表失败也能生成报告
        try:
            # 临床意义分布图
            clinvar_data = {
                'labels': ['Pathogenic', 'Likely pathogenic', 'Uncertain significance', 
                          'Likely benign', 'Benign', 'Unknown'],
                'data': [0, 0, 0, 0, 0, 0]
            }
            
            for v in variants:
                significance = v.get('clinvar_data', {}).get('ClinicalSignificance', 'Unknown')
                if significance in clinvar_data['labels']:
                    index = clinvar_data['labels'].index(significance)
                    clinvar_data['data'][index] += 1
                else:
                    clinvar_data['data'][5] += 1  # Unknown
            
            pdf.add_chart("临床意义分布", "clinvar", clinvar_data)
            
            # PRS分布图
            chrom_counts = {}
            for v in variants:
                chrom = v.get('variant_info', {}).get('chrom', 'Unknown')
                chrom_counts[chrom] = chrom_counts.get(chrom, 0) + 1
            
            prs_data = {
                'labels': list(chrom_counts.keys()),
                'data': list(chrom_counts.values())
            }
            
            pdf.add_chart("染色体变异分布", "prs_distribution", prs_data)
        except Exception as e:
            print(f"生成图表失败: {e}")
            # 添加错误信息到PDF
            pdf.add_section("图表生成失败", [f"图表生成过程中出错: {str(e)}"])
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf.output(tmp.name, 'F')  # 使用output方法保存文件
            tmp_path = tmp.name
        
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=f'breast_cancer_risk_report_{task_id}.pdf',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        print(f"生成报告失败: {e}")
        traceback.print_exc()
        return jsonify({'error': f'报告生成失败: {str(e)}'}), 500
    
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as e:
                print(f"删除临时文件失败: {e}")


# 添加前端路由 fallback
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

# ----------------------------
# Background task processing
# ----------------------------

from app.utils.variant_utils import process_variants
import os
import traceback

def process_vcf_background(task_id, file_path, tasks):
    try:
        print(f"[INFO][{task_id}] 开始解析 VCF 文件: {file_path}")
        tasks[task_id]['task_type'] = 'vcf'
        tasks[task_id]['progress'] = 10
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
        tasks[task_id]['task_type'] = 'vcf'
        tasks[task_id]['error_message'] = str(e)


def process_rsid_background(task_id, rsid, tasks):
    try:
        print(f"[INFO][{task_id}] 开始处理 rsID : {rsid}")
        tasks[task_id]['task_type'] = 'rsid'
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
        tasks[task_id]['task_type'] = 'rsid'
        tasks[task_id]['error_message'] = str(e)


