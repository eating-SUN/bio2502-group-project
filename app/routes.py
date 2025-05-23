from flask import Blueprint, request, jsonify, render_template
from app.utils import vcf_parser, variant_query, bio_features, regulome, prs
import uuid
import threading
import os

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


@main.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Invalid task ID'}), 404
    
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
    task = tasks.get(task_id)
    
    if not task or task['status'] != 'completed':
        return "Task not completed or not found", 404

    result = task['result']['summary']
    
    return render_template(
        'results.html',
        variant_id=result.get('sample_variant', {}).get('id', 'N/A'),
        clinvar_data=result.get('clinvar_data'),
        pro_features=result.get('protein_features'),
        regulome_score=result.get('regulome_score', 'N/A'),
        prs_score=result.get('prs_score'),
        prs_risk=result.get('prs_risk')
    )


# ----------------------------
# Background task processing
# ----------------------------

def process_vcf_background(task_id, file_path):
    try:
        tasks[task_id]['status'] = 'parsing'
        tasks[task_id]['progress'] = 10
        tasks[task_id]['variants'] = variants
        
        # 1. parse vcf file
        variants = vcf_parser.parse(file_path) 
        
        tasks[task_id]['progress'] = 20

        # 2. query ClinVar data
        for variant in variants:
            clinvar_data = variant_query.query_clinvar(variant['id'])
            variant['clinvar_data'] = clinvar_data

        tasks[task_id]['progress'] = 40

        # 3. get protein sequence
        for variant in variants:
            protein_data = variant_query.get_protein_sequence(variant['id'])
            variant['protein_data'] = protein_data

        tasks[task_id]['progress'] = 50

        # 4. calculate protein features
        for variant in variants:
            if 'protein_data' in variant:
                pro_features = bio_features.calculate_protein_features(
                    variant['protein_data']['before'], 
                    variant['protein_data']['after']
                    )
                variant['protein_features'] = pro_features

        tasks[task_id]['progress'] = 60

        # 5. query regulome score
        for variant in variants:
            chrom = variant['clinvar_data'].get('Chromosome')
            start = variant['clinvar_data'].get('Start')
            end = variant['clinvar_data'].get('Stop')
            regulome_score = regulome.query_score({
                'chrom': chrom, 
               'start': start,
                'end': end
                })
            variant['regulome_score'] = regulome_score

        tasks[task_id]['progress'] = 70
        
        # 6. caclulate PRS
        prs_score, matched = prs.compute_prs(variants)
        prs_risk = prs.classify_risk(prs_score)
        
        tasks[task_id]['progress'] = 80


        # 7. save result
        sample_variant = variants[0] if variants else None
        clinvar_data = variant_query.query_clinvar(sample_variant['id']) if sample_variant else None
        
        tasks[task_id]['result'] = {
            'status': 'completed',
            'variants': variants[:100],  # limit to 100 variants
            'summary': {
                'variant_id': sample_variant['id'] if sample_variant else None,
                'protein_features': pro_features,
               'regulome_score': regulome_score,
                'prs_score': prs_score,
                'prs_risk': prs_risk,
                'clinvar_data': clinvar_data
            }
        }
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['progress'] = 100
        
    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
    finally:
        # clean uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)