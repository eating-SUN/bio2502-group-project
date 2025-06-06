import torch
import time
import joblib

def train(model, dataloaders, optimizer, loss_fn, device, num_epochs=10, gene_encoder=None):

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
            
            for i, batch in enumerate(dataloaders[phase]):
                if len(batch) == 4:
                    seqs, genes, masks, labels = batch
                    seqs, genes, masks, labels = seqs.to(device), genes.to(device), masks.to(device), labels.to(device)
                elif len(batch) == 3:
                    seqs, genes, labels = batch
                    seqs, genes, labels = seqs.to(device), genes.to(device), labels.to(device)
                    masks = None
                else:
                    seqs, labels = batch
                    seqs, labels = seqs.to(device), labels.to(device)
                    genes = masks = None

                # 训练时给标签加噪声，增强泛化
                labels = labels + torch.randn_like(labels) * 0.05
                labels = labels.clamp(0, 1)
                
                optimizer.zero_grad()
                
                with torch.set_grad_enabled(phase == 'train'):
                    if genes is not None and masks is not None:
                        outputs = model(seqs, genes, masks)
                    elif genes is not None:
                        outputs = model(seqs, genes)
                    else:
                        outputs = model(seqs)
                    
                    loss = loss_fn(outputs, labels)
                    
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                if phase == 'train' and (i % 400 == 0):
                    print(f"Train batch {i} outputs: "
                          f"mean={outputs.mean():.4f}, std={outputs.std():.4f}, "
                          f"min={outputs.min():.4f}, max={outputs.max():.4f}")

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

    # 训练结束后保存编码器
    if gene_encoder is not None:
        joblib.dump(gene_encoder, "predict/model/gene_encoder.pkl")
        print("Gene encoder saved as gene_encoder.pkl")
    
    return val_loss  # 返回验证损失

