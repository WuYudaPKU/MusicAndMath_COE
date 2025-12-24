import torch
import torch.nn as nn
from model import MelodyTransformer
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt

def train_with_visualization(data_path, model_name):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sequences = torch.load(data_path) 
    loader = DataLoader(TensorDataset(sequences), batch_size=32, shuffle=True)

    model = MelodyTransformer(vocab_size=130).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    loss_history = [] 
    print(f"开始训练 {model_name}...")
    model.train()
    for epoch in range(20):
        total_loss = 0
        for batch in loader:
            x = batch[0].to(device)
            logits = model(x[:, :-1]) 
            loss = criterion(logits.reshape(-1, logits.size(-1)), x[:, 1:].reshape(-1))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(loader)
        loss_history.append(avg_loss)
        print(f"Epoch [{epoch+1}/20], Loss: {avg_loss:.4f}")

    torch.save(model.state_dict(), f"{model_name}.pth")
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, 21), loss_history, marker='o', color='b', label='Training Loss')
    plt.title('Training Loss Convergence')
    plt.xlabel('Epoch')
    plt.ylabel('Cross Entropy Loss')
    plt.grid(True)
    plt.legend()
    plt.savefig("loss_curve.png")
    plt.show()

train_with_visualization("clean_midi_dataset.pt", "lmd_eval")