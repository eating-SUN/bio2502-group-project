import torch
import os
import sqlite3
import pyfaidx
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import Dataset


# 配置参数
DB_PATH = "./data/clinvar/brca_clinvar.db"
FASTA_PATH = "data/GRCh38/Homo_sapiens.GRCh38.dna.primary_assembly.fa"
TABLE_NAME = "brca_clinvar"
MAX_SEQ_LENGTH = 1000  # 1kb序列
CHAR_TO_INDEX = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}

# 字符到索引的映射 (DNA序列)
CHAR_TO_INDEX = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'N': 4}
VOCAB_SIZE = len(CHAR_TO_INDEX) + 1  # +1 for padding index 0

# 确保FASTA索引存在
if not os.path.exists(FASTA_PATH + ".fai"):
    pyfaidx.Faidx(FASTA_PATH)

fasta = pyfaidx.Fasta(FASTA_PATH)

def extract_region(chrom_id, pos, window=MAX_SEQ_LENGTH):
    """提取基因组区域"""
    try:
        chrom = str(chrom_id)
        # 自动适配 FASTA 命名
        if chrom not in fasta:
            # 尝试去掉 chr 前缀再匹配
            if chrom.startswith("chr") and chrom[3:] in fasta:
                chrom = chrom[3:]
            elif f"chr{chrom}" in fasta:
                chrom = f"chr{chrom}"
            else:
                print(f"[WARN] Chromosome {chrom_id} not found in FASTA.")
                return "N" * window

        pos = int(round(pos))  # 确保pos是整数
        start = max(1, pos - window // 2)
        end = start + window - 1
        seq = fasta[chrom][start - 1:end]
        return str(seq).upper()
    
    except Exception as e:
        print(f"[ERROR] Failed to extract region for {chrom_id}:{pos} - {e}")
        return "N" * window


# 从SQLite数据库读取数据
def load_data():
    conn = sqlite3.connect(DB_PATH)
    query = f"""
    SELECT DISTINCT 
        chrom, pos, rsid, ref, alt, gene, 
        consequence, af_exac, af_tgp, clnsig, score
    FROM {TABLE_NAME}
    WHERE score IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


def preprocess_data(df):
    # 确保 pos 是整数
    df['pos'] = pd.to_numeric(df['pos'], errors='coerce')
    df = df.dropna(subset=['pos']).copy()

    # 变异长度：这里用 ref 和 alt 长度差异来简单计算
    df['variant_length'] = df.apply(lambda row: max(len(str(row['ref'])), len(str(row['alt']))), axis=1)

    print("Extracting genomic regions...")
    df['genomic_region'] = df.apply(
        lambda row: extract_region(
            row['chrom'],
            row['pos'],
            window=MAX_SEQ_LENGTH
        ),
        axis=1
    )
    
    # 编码 clnsig（临床意义）标签
    print("Encoding clinical significance labels...")
    # 预定义所有可能的标签（包括你后续预测可能用到的）
    predefined_labels = [
        'Benign',
        'Likely_benign',
        'Uncertain_significance',
        'Likely_pathogenic',
        'Pathogenic'
    ]

    # 确保所有预定义标签在编码器中，即使训练集中某些标签缺失
    all_labels = pd.Series(predefined_labels + df['clnsig'].dropna().astype(str).tolist())

    clnsig_encoder = LabelEncoder()
    clnsig_encoder.fit(all_labels)
    df['clnsig_label'] = clnsig_encoder.transform(df['clnsig'].astype(str))

    # 编码 gene
    print("Encoding gene labels...")
    gene_encoder = LabelEncoder()
    df['gene_encoded'] = gene_encoder.fit_transform(df['gene'].astype(str))

    return df, clnsig_encoder, gene_encoder


def dna_to_tensor(sequence):
    """将DNA序列转换为PyTorch张量"""
    # 截断或填充序列到固定长度
    if len(sequence) > MAX_SEQ_LENGTH:
        sequence = sequence[:MAX_SEQ_LENGTH]
    elif len(sequence) < MAX_SEQ_LENGTH:
        sequence = sequence + 'N' * (MAX_SEQ_LENGTH - len(sequence))
    
    # 转换为索引序列
    indices = [CHAR_TO_INDEX.get(c, CHAR_TO_INDEX['N']) + 1 for c in sequence]
    return torch.tensor(indices, dtype=torch.long)


def get_variant_mask(pos, chrom_seq_start, window=MAX_SEQ_LENGTH):
    """根据变异位置计算在序列中的索引位置"""
    center = chrom_seq_start + window // 2
    variant_idx = window // 2  # 默认中心位置
    mask = torch.zeros(window, dtype=torch.float32)
    if 0 <= variant_idx < window:
        mask[variant_idx] = 1.0
    return mask


# 自定义数据集类
class VariantDataset(Dataset):
    def __init__(self, dataframe, use_gene_encoding=False, use_mask=False):
        self.data = dataframe.reset_index(drop=True)
        self.use_gene = use_gene_encoding
        self.use_mask = use_mask

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        seq = dna_to_tensor(row['genomic_region'])
        score = torch.tensor(row['score'], dtype=torch.float32)

        # 默认占位
        gene_id = None
        variant_mask = None

        if self.use_gene:
            gene_id = torch.tensor(int(row['gene_encoded']), dtype=torch.long)
        
        if self.use_mask:
            variant_mask = get_variant_mask(row['pos'], row['pos'] - MAX_SEQ_LENGTH // 2)

        # 返回 tuple，顺序固定：
        if gene_id is not None and variant_mask is not None:
            return seq, gene_id, variant_mask, score
        elif gene_id is not None:
            return seq, gene_id, score
        else:
            return seq, score
