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
                
                optimizer.zero_grad()
                
                with torch.set_grad_enabled(phase == 'train'):
                    if genes is not None and masks is not None:
                        outputs = model(seqs, genes, masks)
                    elif genes is not None:
                        outputs = model(seqs, genes)
                    else:
                        outputs = model(seqs)
                    
                    outputs_clamped = torch.clamp(outputs, 0, 1)
                    loss = loss_fn(outputs_clamped, labels)
                    
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()
                
                # 只在训练阶段，且每print_freq个batch打印一次（包含第0个batch）
                if phase == 'train' and (i % 400 == 0):
                    print(f"Train batch {i} outputs mean: {outputs_clamped.mean().item():.4f}, "
                          f"std: {outputs_clamped.std().item():.4f}, min: {outputs_clamped.min().item():.4f}, max: {outputs_clamped.max().item():.4f}")
                   
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
    
    return val_loss  # 返回验证损失

