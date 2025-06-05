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
    df_train, df_val = train_test_split(
    df,
    test_size=0.2,
    random_state=42,
    stratify=df["clnsig"]  # 假设类别列名为 "clnsig"
)

    # 检查类别分布
    print("训练集类别分布:")
    print(df_train["clnsig"].value_counts(normalize=True))

    print("\n验证集类别分布:")
    print(df_val["clnsig"].value_counts(normalize=True))

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
    optimizer = torch.optim.Adam(model.parameters(), lr, weight_decay=1e-3)
    loss_fn = nn.MSELoss()

    # 学习率调度器
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.7)

    # best_val_loss = float('inf')
    # patience = 10  # 当验证损失在10个epoch后不再改善，停止训练
    # trigger_times = 0

    for epoch in range(num_epochs):
        print(f"Epoch {epoch+1}/{num_epochs}")
        val_loss = train(model, dataloaders, optimizer, loss_fn, device, num_epochs=1, gene_encoder=gene_encoder, clnsig_encoder=clnsig_encoder)  
        scheduler.step(val_loss)  # 使用验证损失来调整学习率

        # if val_loss < best_val_loss:
        #     best_val_loss = val_loss
        #     trigger_times = 0
        # else:
        #     trigger_times += 1

        # if trigger_times >= patience:
        #     print('Early stopping!')
        #     break

if __name__ == "__main__":
    main()

