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

# 模型参数（需要和训练时一致）
VOCAB_SIZE = 6
EMBED_DIM = 16
GENE_EMBED_DIM = 8
SEQ_LEN = 1000

def load_model():
    # 加载 gene_encoder
    if os.path.exists(GENE_ENCODER_PATH):
        gene_encoder = joblib.load(GENE_ENCODER_PATH)
        gene_num_classes = len(gene_encoder.classes_)
    else:
        gene_encoder = None
        gene_num_classes = None

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
    # 提取 DNA 区域
    chrom = variant['chrom']
    pos = variant['pos']
    seq = extract_region(chrom, pos, window=SEQ_LEN)
    seq_tensor = dna_to_tensor(seq).unsqueeze(0).to(DEVICE)  # (1, L)

    # 基因编码
    gene = variant.get('gene')
    if model.use_gene and gene and gene_encoder and gene in gene_encoder.classes_:
        gene_idx = gene_encoder.transform([gene])[0]
        gene_tensor = torch.tensor([gene_idx], dtype=torch.long).to(DEVICE)
        output = model(seq_tensor, gene_tensor)
    else:
        output = model(seq_tensor)

    score = torch.sigmoid(output).item()
    return score

def predict_variants(model, gene_encoder, variants):
    """
    对多个变异进行PRS风格加权评分。
    参数：
        model: 训练好的 VariantClassifier 模型
        gene_encoder: 基因编码器或 None
        variants: list，多个变异，每个变异是 dict，包含 'ref', 'alt', 'genotype' 等字段
    返回：
        float: 综合得分（PRS式加权平均）
    """
    def compute_alt_dosage(ref, alt, genotype):
        if not genotype or genotype == "NA":
            return 0
        alleles = genotype.replace('|', '/').split('/')
        return alleles.count(alt)

    total_score = 0.0
    total_dosage = 0.0

    with torch.no_grad():
        for var in variants:
            try:
                ref = var.get('ref')
                alt = var.get('alt')
                genotype = var.get('genotype', 'NA')
                dosage = compute_alt_dosage(ref, alt, genotype)
                if dosage == 0:
                    continue

                score = predict_variant(model, gene_encoder, var)
                total_score += score * dosage
                total_dosage += dosage

            except Exception as e:
                print(f"[WARN] 变异 {var.get('id', 'NA')} 预测失败: {e}")
                continue

    # 计算风险等级
    if total_dosage > 0:
        score = total_score / total_dosage
        
        # 根据最终得分确定风险等级
        if score < 0.5:
            risk_level = "低风险"
        elif score < 1.0:
            risk_level = "中等风险"
        elif score < 1.5:
            risk_level = "高风险"
        else:
            risk_level = "极高风险"
            
        return score, risk_level
    else:
        return 0.0, "未评估"




