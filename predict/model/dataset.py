import torch
import os
import sqlite3
import pyfaidx
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm
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
        if chrom not in fasta:
            print(f"[WARN] Chromosome {chrom} not found in FASTA.")
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
    clnsig_encoder = LabelEncoder()
    df['clnsig_label'] = clnsig_encoder.fit_transform(df['clnsig'].astype(str))

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


# 自定义数据集类
class VariantDataset(Dataset):
    def __init__(self, dataframe, use_gene_encoding=False):
        self.data = dataframe.reset_index(drop=True)
        self.use_gene_encoding = use_gene_encoding

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        
        # 提取DNA序列，返回编码序列tensor
        seq_str = extract_region(row['chrom'], row['pos'], window=MAX_SEQ_LENGTH)
        seq_tensor = dna_to_tensor(seq_str)  # 你的dna_to_tensor函数，将序列转为索引张量，长度固定
        
        # 准备标签score（浮点数）
        label = torch.tensor(row['score'], dtype=torch.float)
        
        if self.use_gene_encoding and 'gene_encoded' in self.data.columns:
            gene_feat = torch.tensor(row['gene_encoded'], dtype=torch.long)
            return seq_tensor, gene_feat, label
        else:
            return seq_tensor, label
        

