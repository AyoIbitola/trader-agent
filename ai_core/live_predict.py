import torch
import joblib
from ai_core.informer import SimpleInformer
from utils.model_utils import load_latest_sequence

def predict(pair):
    x, _ = load_latest_sequence(pair)
    scaler = joblib.load(f"models/scalers/{pair}_scaler.pkl")

    model = SimpleInformer(input_dim=5)
    model.load_state_dict(torch.load(f"models/informer_{pair}.pth"))
    model.eval()

    with torch.no_grad():
        pred_scaled = model(x).item()

    pred_close = scaler.inverse_transform([[0, 0, 0, pred_scaled, 0]])[0][3]
    last_close = scaler.inverse_transform(x[0, -1].numpy().reshape(1, -1))[0][3]

    diff = pred_close - last_close
    if diff > 0.1:
        signal = "buy"
    elif diff < -0.1:
        signal = "sell"
    else:
        signal = "hold"

    print(f"{pair}: Last=${last_close:.2f} | Pred=${pred_close:.2f} → Signal: {signal.upper()}")

    return {
        "signal": signal,
        "price": pred_close
    }
