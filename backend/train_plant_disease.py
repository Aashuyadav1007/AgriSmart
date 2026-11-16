import json
import time
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split, Dataset
from torchvision import datasets, transforms, models
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from PIL import Image

from path_config import BACKEND_DIR, MODELS_DIR, DISEASE_MODEL_PATH, DISEASE_CLASSES_PATH

DATASET_DIR = BACKEND_DIR / "data" / "plantvillage_dataset"

# Custom Dataset wrapper to ensure clean transform isolation between Train, Val and Test
class TransformedDataset(Dataset):
    def __init__(self, subset, transform=None):
        self.subset = subset
        self.transform = transform

    def __getitem__(self, index):
        x, y = self.subset[index]
        if self.transform:
            x = self.transform(x)
        return x, y

    def __len__(self):
        return len(self.subset)

def train_disease_classifier(epochs: int = 12, batch_size: int = 16, lr: float = 0.0008):
    print("=" * 65, flush=True)
    print("AgriMind AI - Module 2: Enhanced 12-Class Disease Classifier", flush=True)
    print("Architecture: MobileNetV2 Transfer Learning", flush=True)
    print("=" * 65, flush=True)
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Compute device: {device}", flush=True)
    
    # 1. Image transformations (strictly isolated)
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.2),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # 2. Raw dataset loading without transform (transforms applied via wrapper)
    print(f"\nScanning dataset from: {DATASET_DIR}...", flush=True)
    raw_dataset = datasets.ImageFolder(root=str(DATASET_DIR))
    class_names = raw_dataset.classes
    class_to_idx = raw_dataset.class_to_idx
    idx_to_class = {str(v): k for k, v in class_to_idx.items()}
    
    total_samples = len(raw_dataset)
    num_classes = len(class_names)
    print(f"Total samples: {total_samples} across {num_classes} classes:", flush=True)
    for idx, cname in enumerate(class_names):
        print(f"  [{idx:2d}] {cname}", flush=True)
        
    # Split into Train (70%), Val (15%), Test (15%) for robust evaluation
    val_size = max(int(0.15 * total_samples), num_classes)
    test_size = max(int(0.15 * total_samples), num_classes)
    train_size = total_samples - val_size - test_size
    
    generator = torch.Generator().manual_seed(42)
    raw_train, raw_val, raw_test = random_split(raw_dataset, [train_size, val_size, test_size], generator=generator)
    
    # Wrap with isolated transforms
    train_dataset = TransformedDataset(raw_train, transform=train_transform)
    val_dataset = TransformedDataset(raw_val, transform=val_transform)
    test_dataset = TransformedDataset(raw_test, transform=val_transform)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    print(f"\nPartitions: Train={len(train_dataset)} | Val={len(val_dataset)} | Held-out Test={len(test_dataset)}", flush=True)
    
    # 3. Model Architecture: MobileNetV2
    print("\nInstantiating MobileNetV2 backbone...", flush=True)
    weights = models.MobileNet_V2_Weights.DEFAULT
    model = models.mobilenet_v2(weights=weights)
    
    # Freeze initial feature layers; fine-tune top feature blocks
    for param in model.features[:-4].parameters():
        param.requires_grad = False
        
    num_ftrs = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.35),
        nn.Linear(num_ftrs, 128),
        nn.ReLU(),
        nn.Dropout(p=0.25),
        nn.Linear(128, num_classes)
    )
    model = model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    # 4. Training Loop
    print("\nStarting Training & Validation loop...", flush=True)
    start_time = time.time()
    best_val_loss = float('inf')
    best_val_acc = 0.0
    history = []
    
    for epoch in range(1, epochs + 1):
        # Training
        model.train()
        train_loss = 0.0
        train_correct = 0
        total_train = 0
        
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            train_correct += torch.sum(preds == labels.data).item()
            total_train += inputs.size(0)
            
        scheduler.step()
        epoch_train_loss = train_loss / total_train
        epoch_train_acc = train_correct / total_train
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        total_val = 0
        
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * inputs.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == labels.data).item()
                total_val += inputs.size(0)
                
        epoch_val_loss = val_loss / total_val
        epoch_val_acc = val_correct / total_val
        
        history.append({
            "epoch": epoch,
            "train_loss": round(epoch_train_loss, 4),
            "train_accuracy": round(epoch_train_acc, 4),
            "val_loss": round(epoch_val_loss, 4),
            "val_accuracy": round(epoch_val_acc, 4)
        })
        
        print(f"Epoch {epoch:2d}/{epochs} - Train Loss: {epoch_train_loss:.4f}, Train Acc: {epoch_train_acc*100:.2f}% | Val Loss: {epoch_val_loss:.4f}, Val Acc: {epoch_val_acc*100:.2f}%", flush=True)
        
        # Save best checkpoint
        if epoch_val_acc > best_val_acc or (epoch_val_acc == best_val_acc and epoch_val_loss < best_val_loss):
            best_val_acc = epoch_val_acc
            best_val_loss = epoch_val_loss
            torch.save(model.state_dict(), str(DISEASE_MODEL_PATH))
            print(f"   --> Saved new best checkpoint (Val Acc: {best_val_acc*100:.2f}%)", flush=True)
            
    training_duration = time.time() - start_time
    print(f"\nTraining completed in {training_duration:.2f}s. Best Val Accuracy: {best_val_acc*100:.2f}%", flush=True)
    
    # 5. Formal Evaluation on Held-out Test Set
    print("\nRunning Evaluation on Held-out Test Set...", flush=True)
    model.load_state_dict(torch.load(str(DISEASE_MODEL_PATH), map_location=device))
    model.eval()
    
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy().tolist())
            all_targets.extend(labels.numpy().tolist())
            
    # Calculate metrics
    test_accuracy = float(np.mean(np.array(all_preds) == np.array(all_targets)))
    print(f"Held-out Test Set Accuracy: {test_accuracy * 100:.2f}%\n", flush=True)
    
    # Precision, Recall, F1
    precision, recall, f1, support = precision_recall_fscore_support(
        all_targets, all_preds, labels=list(range(num_classes)), zero_division=0
    )
    
    per_class_metrics = {}
    for i, cname in enumerate(class_names):
        per_class_metrics[cname] = {
            "precision": round(float(precision[i]), 4),
            "recall": round(float(recall[i]), 4),
            "f1_score": round(float(f1[i]), 4),
            "support": int(support[i])
        }
        print(f"  {cname:<30} P: {precision[i]:.2f} | R: {recall[i]:.2f} | F1: {f1[i]:.2f} (n={support[i]})", flush=True)
        
    cm = confusion_matrix(all_targets, all_preds, labels=list(range(num_classes)))
    
    # 6. Save metadata and metrics
    meta = {
        "architecture": "MobileNetV2 Transfer Learning",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_classes": num_classes,
        "class_names": class_names,
        "class_to_idx": class_to_idx,
        "idx_to_class": idx_to_class,
        "training_epochs": epochs,
        "training_time_seconds": round(training_duration, 2),
        "best_val_accuracy": round(best_val_acc, 4),
        "test_accuracy": round(test_accuracy, 4),
        "per_class_metrics": per_class_metrics,
        "confusion_matrix": cm.tolist(),
        "history": history
    }
    
    with open(DISEASE_CLASSES_PATH, "w") as f:
        json.dump(meta, f, indent=2)
        
    print(f"\n[OK] Model saved to: {DISEASE_MODEL_PATH}", flush=True)
    print(f"[OK] Full metadata & evaluation saved to: {DISEASE_CLASSES_PATH}", flush=True)
    return meta

if __name__ == '__main__':
    train_disease_classifier(epochs=12, batch_size=16, lr=0.0008)
