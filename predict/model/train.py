import torch
import time

def train(model, dataloaders, optimizer, loss_fn, device, num_epochs=10):
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
                torch.save(model.state_dict(), "best_model.pth")
                print("Best model saved.")
        
        print()
    
    print("Training complete. Best val loss: {:.4f}".format(best_val_loss))
