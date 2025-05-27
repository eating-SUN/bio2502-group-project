import subprocess
import requests
import re
import os

def run_vep(input_vcf, output_file):
    """
    调用 Ensembl VEP 对输入 VCF 文件进行注释，输出保存为 TSV 格式。
    """
    output_dir = os.path.dirname(output_file)
    output_name = os.path.basename(output_file)
    print("[DEBUG] 准备执行 VEP")
    print("[DEBUG] 输出目录:", output_dir)
    print("[DEBUG] 输出文件名:", output_name)

    cmd = [
        "perl", "/home/zhangyixuan/course/bio2502/bio2502project/ensembl-vep/vep",
        "-i", input_vcf,
        "--cache",
        "--offline",
        "--dir_cache", "/home/zhangyixuan/course/bio2502/bio2502project/.vep",
        "--assembly", "GRCh38",
        "--format", "vcf",
        "--symbol",
        "--uniprot",
        "--fasta", "/home/zhangyixuan/course/bio2502/bio2502project/data/GRCh38/Homo_sapiens.GRCh38.dna.primary_assembly.fa",
        "--hgvs",
        "--protein",
        "--no_stats",
        "--fields", "Uploaded_variation,SYMBOL,Feature,Protein_position,Amino_acids,HGVSp",
        "--tab",
        "--verbose",
        "-o", output_name,
        "--force_overwrite"
    ]
    
    print("[DEBUG] 执行命令:", " ".join(cmd))
    
    try:
        result = subprocess.run(cmd, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        output_path = os.path.join(output_dir, output_name)
        if os.path.exists(output_path):
            print("[DEBUG] 输出文件已创建，大小:", os.path.getsize(output_path))
            print("[DEBUG] 当前工作目录:", os.getcwd())
            print("[DEBUG] 输出目录文件列表:", os.listdir(output_dir))
        else:
            print("[ERROR] 输出文件未创建！")
            print("[DEBUG] 输出目录内容:", os.listdir(output_dir))
        
        print("[VEP stdout]:\n", result.stdout)
        print("[VEP stderr]:\n", result.stderr)

    except subprocess.CalledProcessError as e:
        error_msg = f"VEP运行失败，退出码：{e.returncode}\nstdout:\n{e.stdout}\nstderr:\n{e.stderr}"
        print(error_msg)
        raise RuntimeError(error_msg)


def parse_vep_output(vep_file):
    """
    解析 VEP 注释结果 TSV 文件，提取蛋白质变异信息。
    返回列表，每项为：{ variant_id, protein_id, hgvs_p }
    """
    variants = []
    with open(vep_file) as f:
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            if len(fields) < 7:
                continue
            variant_id, symbol, feature, protein_pos, aa_change, hgvs_p, uniprot_id = fields[:7]
            if hgvs_p and hgvs_p.startswith("p.") and uniprot_id and uniprot_id != '-':
                variants.append({
                    "id": variant_id,
                    "protein_id": uniprot_id,
                    "hgvs_p": hgvs_p
                })

    print(f"[DEBUG] VEP注释解析完成，变异数: {len(variants)}")
    if variants:
        print("[DEBUG] 示例变异:", variants[0])
    return variants


#  protein utils
def get_uniprot_seq(uniprot_id):
    """
    从 UniProt 获取蛋白质序列（FASTA格式），返回纯序列字符串。
    """
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.fasta"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"[ERROR] 获取 UniProt 序列失败: {uniprot_id}, 状态码: {response.status_code}")
            return None
        lines = response.text.splitlines()
        seq = ''.join([line.strip() for line in lines if not line.startswith('>')])
        return seq
    except Exception as e:
        print(f"[EXCEPTION] 获取 UniProt 序列失败: {uniprot_id}, 错误信息: {e}")
        return None


def parse_hgvs_protein(hgvs_p):
    """
    解析 HGVS.p 格式（如 p.Arg97Cys），返回 (原氨基酸, 位置, 变异氨基酸)
    """
    aa3to1 = {
        'Ala': 'A', 'Arg': 'R', 'Asn': 'N', 'Asp': 'D', 'Cys': 'C',
        'Glu': 'E', 'Gln': 'Q', 'Gly': 'G', 'His': 'H', 'Ile': 'I',
        'Leu': 'L', 'Lys': 'K', 'Met': 'M', 'Phe': 'F', 'Pro': 'P',
        'Ser': 'S', 'Thr': 'T', 'Trp': 'W', 'Tyr': 'Y', 'Val': 'V',
        'Ter': '*'
    }

    hgvs_p = hgvs_p.replace("(", "").replace(")", "")
    match = re.match(r'p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2})', hgvs_p)
    if not match:
        print(f"[WARN] 无法解析 HGVS 表达式: {hgvs_p}")
        return None, None, None

    ref = aa3to1.get(match.group(1))
    pos = int(match.group(2))
    alt = aa3to1.get(match.group(3))

    if ref is None or alt is None:
        print(f"[WARN] 无法识别的氨基酸: {match.group(1)} 或 {match.group(3)}")
    return ref, pos, alt


def mutate_sequence(seq, pos, alt_aa):
    """
    返回突变后的序列。
    参数 pos 为 1-based 索引。
    """
    if not seq or alt_aa is None or pos < 1 or pos > len(seq):
        print(f"[ERROR] 突变位置无效或序列为空: pos={pos}, alt_aa={alt_aa}")
        return None
    seq_list = list(seq)
    seq_list[pos - 1] = alt_aa
    return ''.join(seq_list)
