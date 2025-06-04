import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from model.dataset import VariantDataset, load_data, preprocess_data
from model.model import VariantClassifier
from model.train import train

TRAIN_CONFIG = {
    'batch_size': 32,
    'learning_rate': 1e-3,
    'num_epochs': 100,
    'device': 'cuda' if torch.cuda.is_available() else 'cpu',
}

batch_size = TRAIN_CONFIG['batch_size']
lr = TRAIN_CONFIG['learning_rate']
num_epochs = TRAIN_CONFIG['num_epochs']
device = TRAIN_CONFIG['device']

def main():
    # 1. 加载数据
    df = load_data()

    # 2. 预处理数据，得到编码器等
    df, clnsig_encoder, gene_encoder = preprocess_data(df)

    # 3. 分割训练和验证集
    df_train, df_val = train_test_split(df, test_size=0.2, random_state=42)

    # 4. 创建数据集对象
    train_dataset = VariantDataset(df_train, use_gene_encoding=True)
    val_dataset = VariantDataset(df_val, use_gene_encoding=True)

    # 5. 创建数据加载器
    train_loader = DataLoader(train_dataset, batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size)

    dataloaders = {
        'train': train_loader,
        'val': val_loader
    }

    # 6. 初始化模型，放到设备
    model = VariantClassifier(gene_num_classes=len(gene_encoder.classes_))  # 如果你的模型需要gene类别数
    model.to(device)

    # 7. 定义优化器和损失函数
    optimizer = torch.optim.Adam(model.parameters(), lr)
    loss_fn = nn.MSELoss()

    # 学习率调度器，StepLR每5轮lr减小为原来的0.9倍
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.9)

    for epoch in range(num_epochs):
        print(f"Epoch {epoch+1}/{num_epochs}")
        train(model, dataloaders, optimizer, loss_fn, device, 1)  # 训练1个epoch
        scheduler.step() 

if __name__ == "__main__":
    main()
