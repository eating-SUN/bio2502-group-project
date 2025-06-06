import torch
import torch.nn as nn
import torch.nn.functional as F


class VariantClassifier(nn.Module):
    def __init__(self, vocab_size=6, embed_dim=16, gene_num_classes=None, gene_embed_dim=8, seq_len=1000):
        super(VariantClassifier, self).__init__()
        
        self.seq_embedding = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embed_dim, padding_idx=0)
        
        self.conv1 = nn.Conv1d(in_channels=embed_dim, out_channels=32, kernel_size=7, padding=3)
        self.bn1 = nn.BatchNorm1d(32)
        self.pool = nn.MaxPool1d(kernel_size=4)
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(64)

        self.use_gene = gene_num_classes is not None
        if self.use_gene:
            self.gene_embedding = nn.Embedding(num_embeddings=gene_num_classes, embedding_dim=gene_embed_dim)
        else:
            self.gene_embedding = None

        self.use_mask = True  # 启用 variant_mask 支持

        self.conv_out_dim = self._get_conv_output(seq_len)
        if self.use_mask:
            self.conv_out_dim += 64  # 额外的 masked 区域聚合向量

        fc_input_dim = self.conv_out_dim
        if self.use_gene:
            fc_input_dim += gene_embed_dim

        self.fc1 = nn.Linear(fc_input_dim, 128)
        self.bn3 = nn.BatchNorm1d(128)
        self.dropout1 = nn.Dropout(p=0.5)
        self.fc2 = nn.Linear(128, 1)
        self.sigmoid = nn.Sigmoid()
        self.dropout2 = nn.Dropout(p=0.5)

    def _get_conv_output(self, seq_len):
        with torch.no_grad():
            x = torch.zeros(1, seq_len).long()
            x = self.seq_embedding(x).permute(0, 2, 1)
            x = F.relu(self.bn1(self.conv1(x)))
            x = self.pool(x)
            x = F.relu(self.bn2(self.conv2(x)))
            x = self.pool(x)
            return x.view(1, -1).size(1)

    def forward(self, seq, gene=None, variant_mask=None):
        x = self.seq_embedding(seq).permute(0, 2, 1)
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool(x)
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool(x)

        if variant_mask is not None:
            mask = variant_mask.unsqueeze(1).float()
            mask = self.pool(mask)
            mask = self.pool(mask)
            masked_feature = (x * mask).sum(dim=2)  # (B, C)
            x = x.view(x.size(0), -1)
            x = torch.cat([x, masked_feature], dim=1)
        else:
            x = x.view(x.size(0), -1)

        if self.use_gene and gene is not None:
            gene_embed = self.gene_embedding(gene)
            x = torch.cat([x, gene_embed], dim=1)

        x = F.relu(self.bn3(self.fc1(x)))
        x = self.dropout1(x)
        x = self.fc2(x)              
        return x.squeeze(1)                      
