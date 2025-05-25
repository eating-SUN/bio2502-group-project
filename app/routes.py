from flask import Blueprint, request, jsonify, render_template
from app.utils import vcf_parser, variant_query, regulome, prs#bio_features, 
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
    return render_template('results.html')

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
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Invalid task ID'}), 404
    if task['status'] == 'failed':
        return jsonify({'status': 'failed', 'error_message': task.get('error_message')}), 500
    
    response = {
        'status': task['status'],
        'progress': task.get('progress', 0)
    }
    
    if task['status'] == 'completed':
        response['result'] = task.get('result')

    return jsonify(response)


@main.route('/results', methods=['GET'])
def results():
    task_id = request.args.get('task_id')
    return render_template(
        'results.html'
    )


# ----------------------------
# Background task processing
# ----------------------------

def process_vcf_background(task_id, file_path):
    try:
        tasks[task_id]['status'] = 'parsing'
        tasks[task_id]['progress'] = 10
        
        
        # 1. parse vcf file
        variants = vcf_parser.process_vcf(file_path)  
        tasks[task_id]['progress'] = 30

        # 2. query ClinVar data
        for v in variants:
            if 'variant_info' in v:
                clinvar_data = variant_query.query_clinvar(v['variant_info']['id'])
                v['clinvar_data'] = clinvar_data

        tasks[task_id]['progress'] = 40

        # 3. calculate protein features
        for v in variants:
            if 'protein_info' in v and v['protein_info']:
                pro_features = bio_features.calculate_protein_features(
                    v['protein_info']['wt_seq'], 
                    v['protein_info']['mut_seq']
                    )
                v['protein_features'] = pro_features

        tasks[task_id]['progress'] = 60

        # 5. query regulome score
        for v in variants:
            if 'clinvar_data' in v:
                chrom = v['clinvar_data'].get('Chromosome')
                start = v['clinvar_data'].get('Start')
                end = v['clinvar_data'].get('Stop')
                regulome_score = regulome.query_score({
                    'chrom': chrom, 
                    'start': start,
                    'end': end
                    })
                v['regulome_score'] = regulome_score

        tasks[task_id]['progress'] = 70
        
        # 6. caclulate PRS
        prs_score, matched = prs.compute_prs(variants)
        prs_risk = prs.classify_risk(prs_score)
        
        tasks[task_id]['progress'] = 80


        # 7. save result
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
    
    except Exception as e:
        print('分析任务异常:', e)
        traceback.print_exc()
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['progress'] = 100
        tasks[task_id]['error_message'] = str(e)
    
    finally:
        # clean uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)