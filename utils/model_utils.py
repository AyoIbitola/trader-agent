import pandas as pd
import numpy as np
import torch
import joblib
from sklearn.preprocessing import MinMaxScaler
from pathlib import Path


def preprocess_pair(pair: str, lookback=48, pred_step=1):
    
    path = f"data/{pair}.csv"
    df = pd.read_csv(path)
    df = df[["open", "high", "low", "close", "volume"]]

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df)

    
    Path("models/scalers/").mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, f"models/scalers/{pair}_scaler.pkl")

    X, y = [], []
    for i in range(lookback, len(scaled) - pred_step):
        X.append(scaled[i - lookback:i])
        y.append(scaled[i + pred_step][3])  # predict 'close'

    X = torch.tensor(np.array(X), dtype=torch.float32)
    y = torch.tensor(np.array(y), dtype=torch.float32)

    return X, y


def load_latest_sequence(pair: str, lookback=48):
   
    df = pd.read_csv(f"data/{pair}.csv")
    df = df[["open", "high", "low", "close", "volume"]]

    
    scaler_path = f"models/scalers/{pair}_scaler.pkl"
    scaler = joblib.load(scaler_path)

    scaled = scaler.transform(df)
    recent_seq = scaled[-lookback:]
    recent_seq = torch.tensor(recent_seq, dtype=torch.float32).unsqueeze(0)  # shape: (1, lookback, 5)

    return recent_seq, scaler
