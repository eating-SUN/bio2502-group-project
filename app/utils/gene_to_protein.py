import subprocess
import requests
import time
import urllib.parse
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
        "perl", "/mnt/c/Users/10188/bio2502project/ensembl-vep/vep",
        "-i", input_vcf,
        "--cache",
        "--offline",
        "--dir_cache", "/mnt/c/Users/10188/bio2502project/.vep",
        "--assembly", "GRCh38",
        "--symbol",
        "--uniprot",
        "--fasta", "/home/zhangyixuan/course/bio2502/bio2502project/data/GRCh38/Homo_sapiens.GRCh38.dna.primary_assembly.fa",
        "--hgvs",
        "--protein",
        "--no_stats",
        "--everything",
        "--verbose",
        "-o", output_name,
        "--force_overwrite"
 ]
    
    try:
        result = subprocess.run(cmd, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        output_path = os.path.join(output_dir, output_name)
        if os.path.exists(output_path):
            print("[DEBUG] 输出文件已创建，大小:", os.path.getsize(output_path))
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


def parse_vep_output(vep_file, verbose=True):
    variants = []
    headers = None
    idx_map = {}

    with open(vep_file) as f:
        for line in f:
            if line.startswith("#"):
                if line.startswith("#Uploaded_variation"):
                    headers = line.lstrip("#").strip().split("\t")
                    if verbose:
                        print("[DEBUG] VEP 文件头字段:", headers)

                    for field in ["Uploaded_variation", "Feature_type", "Extra"]:
                        try:
                            idx_map[field] = headers.index(field)
                        except ValueError:
                            idx_map[field] = None
                    if verbose:
                        print(f"[DEBUG] 字段索引映射: {idx_map}")
                continue

            if not headers:
                continue

            fields = line.strip().split("\t")
            if len(fields) < 1:
                continue

            def get_field(name):
                idx = idx_map.get(name)
                if idx is not None and idx < len(fields):
                    return fields[idx]
                return None

            variant_id = get_field("Uploaded_variation")
            feature_type = get_field("Feature_type")
            extra = get_field("Extra")

            if feature_type != "Transcript":
                continue

            protein_id = None
            hgvs_p = None

            if extra:
                extra_dict = dict()
                for kv in extra.split(";"):
                    if '=' in kv:
                        k, v = kv.split("=", 1)
                        extra_dict[k] = v  

                # 直接用原始大小写键名访问
                protein_id = extra_dict.get("SWISSPROT") or extra_dict.get("UniProtKB_ID")
                hgvs_p = extra_dict.get("HGVSp")
                if not protein_id:
                    print(f"[WARNING] 变异 {variant_id} 缺少 protein_id，标记为无法处理")
                    variants.append({
                        "id": variant_id,
                        "protein_id": None,
                        "hgvs_p": hgvs_p
                    })
                    continue

            if verbose:
                print(f"[DEBUG] variant_id={variant_id}, protein_id={protein_id}, hgvs_p={hgvs_p}")

            if hgvs_p and ":" in hgvs_p:
                hgvs_p = hgvs_p.split(":", 1)[1]

            if protein_id and hgvs_p and hgvs_p.startswith("p."):
                variants.append({
                    "id": variant_id,
                    "protein_id": protein_id,
                    "hgvs_p": hgvs_p
                })

    print(f"[DEBUG] VEP注释解析完成，变异数: {len(variants)}")
    if variants:
        print("[DEBUG] 示例变异:", variants[0])
    return variants


#  protein utils
def get_uniprot_seq(uniprot_id, retries=1, timeout=3):
    """
    从 UniProt 获取蛋白质序列（FASTA格式），返回纯序列字符串。
    """
    # 去除 isoform 后缀
    uniprot_id = uniprot_id.split('.')[0]
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.fasta"

    for attempt in range(retries + 1): 
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                lines = response.text.splitlines()
                seq = ''.join([line.strip() for line in lines if not line.startswith('>')])
                return seq
            elif 400 <= response.status_code < 500:
                print(f"[ERROR] UniProt请求失败（客户端错误 {response.status_code}）：{uniprot_id}")
                break  # 不重试 4xx 错误
            else:
                print(f"[WARNING] UniProt响应异常（{response.status_code}），正在重试 {attempt+1}/{retries}...")
        except Exception as e:
            print(f"[EXCEPTION] 请求失败（第 {attempt+1}/{retries} 次）: {e}")
        time.sleep(1)  # 重试等待时间为1秒

    print(f"[ERROR] 获取 UniProt 序列失败：{uniprot_id}")
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
    hgvs_p = urllib.parse.unquote(hgvs_p)
    if not hgvs_p.startswith("p."):
        return None, None, None
    hgvs = hgvs_p[2:].replace("(", "").replace(")", "")

    # missense/nonsense: p.Glu6Val, p.Trp26Ter
    match = re.match(r"([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2}|Ter)", hgvs)
    if match:
        ref = aa3to1.get(match.group(1))
        pos = int(match.group(2))
        alt = aa3to1.get(match.group(3))
        if alt == '*':
            mutation_type = 'nonsense'
        else:
            mutation_type = 'missense'
        return pos, ref, alt, mutation_type
    
    # synonymous: p.Glu7=
    match = re.match(r"([A-Z][a-z]{2})(\d+)=+", hgvs)
    if match:
        ref = aa3to1.get(match.group(1))
        pos = int(match.group(2))
        alt = "="
        mutation_type = "synonymous"
        return pos, ref, alt, mutation_type
    
    # frameshift: p.Phe508LeufsTer19
    match = re.match(r"([A-Z][a-z]{2})(\d+)fs", hgvs)
    if match:
        ref = aa3to1.get(match.group(1))
        pos = int(match.group(2))
        alt = "fs"
        mutation_type = "frameshift"
        return pos, ref, alt, mutation_type
    
    # deletion: p.Lys76del
    match = re.match(r"([A-Z][a-z]{2})(\d+)del", hgvs)
    if match:
        ref = aa3to1.get(match.group(1))
        pos = int(match.group(2))
        alt = "del"
        mutation_type = "deletion"
        return pos, ref, alt, mutation_type
    
    # insertion: p.Lys76_Gly77insArg
    match = re.match(r"([A-Z][a-z]{2})(\d+)_([A-Z][a-z]{2})(\d+)ins([A-Z][a-z]+)", hgvs)
    if match:
        ref = f"{match.group(1)}_{match.group(3)}"
        pos = int(match.group(2))
        alt = f"ins{match.group(5)}"
        mutation_type = "insertion"
        return pos, ref, alt, mutation_type
    
    # delins: p.Lys76delinsArgGly
    match = re.match(r"([A-Z][a-z]{2})(\d+)delins([A-Z][a-z]+)", hgvs)
    if match:
        ref = aa3to1.get(match.group(1))
        pos = int(match.group(2))
        alt = f"delins{match.group(3)}"
        mutation_type = "delins"
        return pos, ref, alt, mutation_type
    
    if hgvs_p in ["p.?", "p.0?"]:
        print(f"[WARN] HGVS 表达式不明确，跳过: {hgvs_p}")
        return None, None, None, "unknown"
    
    print(f"[WARN] 无法解析 HGVS 表达式: {hgvs_p}")
    return None, None, None, None


def mutate_sequence(seq, pos, alt_aa):
    """
    返回突变后的序列。
    参数 pos 为 1-based 索引。
    """

    aa3to1 = {
        'Ala': 'A', 'Arg': 'R', 'Asn': 'N', 'Asp': 'D', 'Cys': 'C',
        'Glu': 'E', 'Gln': 'Q', 'Gly': 'G', 'His': 'H', 'Ile': 'I',
        'Leu': 'L', 'Lys': 'K', 'Met': 'M', 'Phe': 'F', 'Pro': 'P',
        'Ser': 'S', 'Thr': 'T', 'Trp': 'W', 'Tyr': 'Y', 'Val': 'V',
        'Ter': '*'
    }

    if not seq or alt_aa is None or pos < 1 or pos > len(seq):
        print(f"[ERROR] 突变位置无效或序列为空: pos={pos}, alt_aa={alt_aa}")
        return None
    
    if alt_aa in ['=', None]:
        print(f"[DEBUG] 同义突变，无需修改序列: pos={pos}, alt_aa={alt_aa}")
        return seq
    
    if alt_aa == 'fs':
        print(f"[DEBUG] 移码突变，从位置 {pos} 开始截断")
        return seq[:pos] + "*"
    
    if alt_aa == 'del':
        print(f"[DEBUG] 缺失突变，删除位置 {pos} 氨基酸")
        return seq[:pos - 1] + seq[pos:]
    
    if alt_aa.startswith("ins"):
        insertion = ''.join([aa3to1.get(alt_aa[i:i+3], '') for i in range(3, len(alt_aa), 3)])
        print(f"[DEBUG] 插入突变，在位置 {pos} 后插入: {insertion}")
        return seq[:pos] + insertion + seq[pos:]

    if alt_aa.startswith("delins"):
        print(f"[DEBUG] 删除插入突变，位置 {pos} 替换为 {alt_aa}")
        replacement = ''.join([aa3to1.get(alt_aa[i:i+3], '') for i in range(7, len(alt_aa), 3)])
        return seq[:pos - 1] + replacement + seq[pos:]

    if len(alt_aa) == 1:
        seq_list = list(seq)
        seq_list[pos - 1] = alt_aa
        return ''.join(seq_list)

    print(f"[WARN] 未知的变异类型: pos={pos}, alt_aa={alt_aa}")
    return None
