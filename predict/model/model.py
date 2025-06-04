import torch
import torch.nn as nn
import torch.nn.functional as F


class VariantClassifier(nn.Module):
    def __init__(self, vocab_size=6, embed_dim=16, gene_num_classes=None, gene_embed_dim=8, seq_len=1000):
        super(VariantClassifier, self).__init__()
        
        self.seq_embedding = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embed_dim, padding_idx=0)
        
        self.conv1 = nn.Conv1d(in_channels=embed_dim, out_channels=32, kernel_size=7, padding=3)
        self.pool = nn.MaxPool1d(kernel_size=4)
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, padding=2)

        self.use_gene = gene_num_classes is not None
        if self.use_gene:
            self.gene_embedding = nn.Embedding(num_embeddings=gene_num_classes, embedding_dim=gene_embed_dim)
        else:
            self.gene_embedding = None

        fc_input_dim = self._get_conv_output(seq_len)
        if self.use_gene:
            fc_input_dim += gene_embed_dim

        self.fc1 = nn.Linear(fc_input_dim, 128)
        self.dropout = nn.Dropout(p=0.5)  # 加dropout
        self.fc2 = nn.Linear(128, 1)

    def _get_conv_output(self, seq_len):
        x = torch.zeros(1, seq_len).long()
        x = self.seq_embedding(x).permute(0, 2, 1)
        x = F.relu(self.conv1(x))
        x = self.pool(x)
        x = F.relu(self.conv2(x))
        x = self.pool(x)
        return x.view(1, -1).size(1)

    def forward(self, seq, gene=None):
        x = self.seq_embedding(seq).permute(0, 2, 1)
        x = F.relu(self.conv1(x))
        x = self.pool(x)
        x = F.relu(self.conv2(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)

        if self.use_gene and gene is not None:
            gene_embed = self.gene_embedding(gene)
            x = torch.cat([x, gene_embed], dim=1)

        x = F.relu(self.fc1(x))
        x = self.dropout(x)  # dropout只在训练时生效
        out = self.fc2(x)
        return out.squeeze(1)
