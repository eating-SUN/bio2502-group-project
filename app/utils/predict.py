import torch
import torch.nn.functional as F
import joblib
import os
from predict.model.model import VariantClassifier
from predict.model.dataset import extract_region, dna_to_tensor

# 加载模型和编码器
MODEL_PATH = 'predict/model/best_model.pth'
GENE_ENCODER_PATH = 'predict/model/gene_encoder.pkl'
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 模型参数（和训练时一致）
VOCAB_SIZE = 6
EMBED_DIM = 16
GENE_EMBED_DIM = 8
SEQ_LEN = 1000

CLNSIG_SCORE = {
    'Benign': 0.0,
    'Likely_benign': 0.05,
    'Uncertain_significance': 0.25,
    'Likely_pathogenic': 0.7,
    'Pathogenic': 1.0
}

def load_model():
    # 加载 gene_encoder
    if os.path.exists(GENE_ENCODER_PATH):
        gene_encoder = joblib.load(GENE_ENCODER_PATH)
        gene_num_classes = len(gene_encoder.classes_)
    else:
        raise ValueError("gene_encoder.pkl not found. You must use the same encoder as during training.")

    # 初始化模型
    model = VariantClassifier(
        vocab_size=VOCAB_SIZE,
        embed_dim=EMBED_DIM,
        gene_num_classes=gene_num_classes,
        gene_embed_dim=GENE_EMBED_DIM,
        seq_len=SEQ_LEN
    )
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()

    return model, gene_encoder


def predict_variant(model, gene_encoder, variant):
    chrom = variant['chrom']
    pos = variant['pos']
    seq = extract_region(chrom, pos, window=SEQ_LEN)
    if seq.count('N') / len(seq) > 0.5:
        print(f"[DEBUG] 变异 {variant['id']}：序列 N 比例过高 ({seq.count('N') / len(seq):.2f})")

    seq_tensor = dna_to_tensor(seq).unsqueeze(0).to(DEVICE)

    gene = variant.get('gene')

    if model.use_gene:
        if gene_encoder and isinstance(gene, str) and gene in gene_encoder.classes_:
            gene_idx = gene_encoder.transform([gene])[0]
        else:
            gene_idx = 0  # 未知基因编码为 0
        gene_tensor = torch.tensor([gene_idx], dtype=torch.long).to(DEVICE)
        output = model(seq_tensor, gene_tensor)
    else:
        output = model(seq_tensor)

    score = torch.sigmoid(output).item()
    # 分类标签：选择最接近的 CLNSIG
    closest_label = min(CLNSIG_SCORE.items(), key=lambda x: abs(score - x[1]))[0]

    print(f"[DEBUG] 变异 {variant['id']} 预测得分: {score:.4f} 预测标签: {closest_label}")
    return score, closest_label


def compute_alt_dosage(ref, alt, genotype):
    if not genotype or genotype == "NA":
        return 0
    alleles = genotype.replace('|', '/').split('/')
    return alleles.count(alt)
