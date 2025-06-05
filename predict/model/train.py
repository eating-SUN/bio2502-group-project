import torch
import time
import joblib

def train(model, dataloaders, optimizer, loss_fn, device, num_epochs=10, gene_encoder=None, clnsig_encoder=None):
    """
    model: PyTorch模型
    dataloaders: dict，包含 'train' 和 'val' 的 DataLoader
    optimizer: 优化器
    loss_fn: 损失函数
    device: 'cuda'或'cpu'
    num_epochs: 训练轮数
    """
    model.to(device)
    
    best_val_loss = float('inf')
    val_loss = float('inf')  # 添加这个变量来存储当前epoch的验证损失
    
    for epoch in range(1, num_epochs + 1):
        print(f"Epoch {epoch}/{num_epochs}")
        print("-" * 20)
        
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()
            
            running_loss = 0.0
            total_samples = 0
            
            start_time = time.time()
            
            for batch in dataloaders[phase]:
                # 处理输入
                if len(batch) == 3:
                    seqs, genes, labels = batch
                    seqs = seqs.to(device)
                    genes = genes.to(device)
                    labels = labels.to(device)
                else:
                    seqs, labels = batch
                    seqs = seqs.to(device)
                    labels = labels.to(device)
                    genes = None
                
                optimizer.zero_grad()
                
                with torch.set_grad_enabled(phase == 'train'):
                    if genes is not None:
                        outputs = model(seqs, genes)
                    else:
                        outputs = model(seqs)
                    
                    loss = loss_fn(outputs, labels)
                    
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()
                
                running_loss += loss.item() * seqs.size(0)
                total_samples += seqs.size(0)
            
            epoch_loss = running_loss / total_samples
            elapsed = time.time() - start_time
            
            print(f"{phase} Loss: {epoch_loss:.4f}  Time: {elapsed:.1f}s")
            
            # 保存最优模型
            if phase == 'val' and epoch_loss < best_val_loss:
                best_val_loss = epoch_loss
                torch.save(model.state_dict(), "predict/model/best_model.pth")
                print("Best model saved.")
            
            if phase == 'val':
                val_loss = epoch_loss  # 在验证阶段更新val_loss
        
        print()
    
    print("Training complete. Best val loss: {:.4f}".format(best_val_loss))

    # 训练结束后保存编码器（如果有）
    if gene_encoder is not None:
        joblib.dump(gene_encoder, "predict/model/gene_encoder.pkl")
        print("Gene encoder saved as gene_encoder.pkl")
    if clnsig_encoder is not None:
        joblib.dump(clnsig_encoder, "predict/model/clnsig_encoder.pkl")
        print("Clinical significance encoder saved as clnsig_encoder.pkl")
    
    return val_loss  # 返回验证损失
