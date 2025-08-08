

import time
from ai_core.live_predict import predict
from utils.data_fetcher import fetch_pair

pairs = ["XAU_USD", "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]

while True:
    for pair in pairs:
        fetch_pair(pair)
        signal = predict(pair)
        if signal != "hold":
            print(f"🫵 ACTION REQUIRED: {pair} → {signal} NOW")
    print(" Sleeping 5 minutes...\n")
    time.sleep(300)
