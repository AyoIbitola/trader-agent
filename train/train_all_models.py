import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from utils.model_utils import preprocess_pair
from ai_core.informer import SimpleInformer

def train_model(pair, epochs=10, lr=1e-3):
    X, y = preprocess_pair(pair)
    dataset = DataLoader(TensorDataset(X, y), batch_size=64, shuffle=True)

    model = SimpleInformer(input_dim=5)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        losses = []
        for xb, yb in dataset:
            pred = model(xb).squeeze()
            loss = criterion(pred, yb)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        print(f"{pair} | Epoch {epoch+1} | Loss: {sum(losses)/len(losses):.4f}")

    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), f"models/informer_{pair}.pth")
    print(f"Saved model: informer_{pair}.pth")

if __name__ == "__main__":
    for p in ["XAU_USD", "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]:
        train_model(p)
