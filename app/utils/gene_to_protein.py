import subprocess
import requests
import re
import os

def run_vep(input_vcf, output_file):
    """
    调用 Ensembl VEP 对输入 VCF 文件进行注释，输出保存为 TSV 格式。
    """
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    # vep_path = os.path.join(project_root, "ensembl-vep", "vep")
    
    cmd = [
        "perl", "./ensembl-vep/vep",
        "-i", input_vcf,
        "--cache",
        "--offline",
        "--dir_cache", "./.vep",
        "--assembly", "GRCh38",
        "--format", "vcf",
        "--symbol",
        "--uniprot",
        "--fasta", "./data/GRCh38/Homo_sapiens.GRCh38.dna.primary_assembly.fa",
        "--hgvs",
        "--protein",
        "--vcf_info_field", "CSQ",
        "--fields", "Uploaded_variation,SYMBOL,Feature,Protein_position,Amino_acids,HGVSp",
        "--tab",
        "--verbose",
        "-o", output_file
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("[VEP stdout]:\n", result.stdout)
        print("[VEP stderr]:\n", result.stderr)
    except subprocess.CalledProcessError as e:
        print("[ERROR] VEP运行失败，退出码：", e.returncode)
        print("[VEP stdout]:\n", e.stdout)
        print("[VEP stderr]:\n", e.stderr)
        raise 

def parse_vep_output(vep_file):
    """
    解析 VEP 注释结果 TSV 文件，提取蛋白质变异信息。
    返回列表，每项为：{ protein_id, hgvs_p }
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
            if hgvs_p.startswith("ENSP") or hgvs_p.startswith("p."):
                variants.append({
                    "id": variant_id,
                    "protein_id": uniprot_id,
                    "hgvs_p": hgvs_p
                })
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
            print(f"Failed to fetch UniProt sequence for {uniprot_id}, status code: {response.status_code}")
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
    aa3to1 = {'Ala':'A','Arg':'R','Asn':'N','Asp':'D','Cys':'C',
              'Glu':'E','Gln':'Q','Gly':'G','His':'H','Ile':'I',
              'Leu':'L','Lys':'K','Met':'M','Phe':'F','Pro':'P',
              'Ser':'S','Thr':'T','Trp':'W','Tyr':'Y','Val':'V',
              'Ter': '*'}
    
    # 匹配格式 p.Arg97Cys 或 p.Arg97Ter
    hgvs_p = hgvs_p.replace("(", "").replace(")", "")
    match = re.match(r'p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2})', hgvs_p)
    if not match:
        return None, None, None
    ref = aa3to1.get(match.group(1))
    pos = int(match.group(2))
    alt = aa3to1.get(match.group(3))
    return ref, pos, alt

def mutate_sequence(seq, pos, alt_aa):
    """
    返回发生突变后的序列。
    参数 pos 为 1-based 索引。
    """
    if alt_aa is None or pos < 1 or pos > len(seq):
        return None
    seq_list = list(seq)
    seq_list[pos - 1] = alt_aa
    return ''.join(seq_list)
