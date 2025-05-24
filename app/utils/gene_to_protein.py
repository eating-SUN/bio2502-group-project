import subprocess
import requests
import re

def run_vep(input_vcf, output_file):
    """
    调用 Ensembl VEP 对输入 VCF 文件进行注释，输出保存为 TSV 格式。
    """
    cmd = [
        "vep",
        "-i", input_vcf,
        "--cache",
        "--offline",
        "--assembly", "GRCh38",
        "--format", "vcf",
        "--symbol",
        "--hgvs",
        "--protein",
        "--vcf_info_field", "CSQ",
        "--fields", "SYMBOL,Feature,Protein_position,Amino_acids,HGVSp",
        "--tab",
        "-o", output_file
    ]
    subprocess.run(cmd, check=True)

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
            if len(fields) < 5:
                continue
            symbol, feature, protein_pos, aa_change, hgvs_p = fields[:5]
            if hgvs_p.startswith("ENSP") or hgvs_p.startswith("p."):
                variants.append({
                    "protein_id": feature,
                    "hgvs_p": hgvs_p
                })
    return variants


#  protein utils

def get_uniprot_seq(uniprot_id):
    """
    从 UniProt 获取蛋白质序列（FASTA格式），返回纯序列字符串。
    """
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.fasta"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    lines = response.text.splitlines()
    seq = ''.join([line.strip() for line in lines if not line.startswith('>')])
    return seq

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
    if pos < 1 or pos > len(seq):
        return None
    seq_list = list(seq)
    seq_list[pos - 1] = alt_aa
    return ''.join(seq_list)
