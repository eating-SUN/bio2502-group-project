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
    'num_epochs': 70,
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
        stratify=df["clnsig"]
    )

    # 4. 创建数据集对象，启用基因编码和变异掩码
    train_dataset = VariantDataset(df_train, use_gene_encoding=True, use_mask=True)
    val_dataset = VariantDataset(df_val, use_gene_encoding=True, use_mask=True)

    # 5. 创建数据加载器
    train_loader = DataLoader(
    train_dataset,
    batch_size=batch_size,
    shuffle=True,
    num_workers=4,      # 多进程加载数据，避免主线程阻塞
    pin_memory=True     # 加快数据从CPU到GPU的传输速度
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )

    dataloaders = {'train': train_loader, 'val': val_loader}

    # 6. 初始化模型，注意传入gene类别数和是否使用mask
    model = VariantClassifier(gene_num_classes=len(gene_encoder.classes_))
    model.to(device)

    # 7. 定义优化器和损失函数
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.MSELoss()

    # 8. 学习率调度器
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.8)

    for epoch in range(num_epochs):
        print(f"Epoch {epoch+1}/{num_epochs}")
        val_loss = train(
            model,
            dataloaders,
            optimizer,
            loss_fn,
            device,
            num_epochs=1,
            gene_encoder=gene_encoder
        )
        scheduler.step(val_loss)

    print("训练完成。")

if __name__ == "__main__":
    main()