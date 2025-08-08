import os
import pandas as pd 
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
from dotenv import load_dotenv

load_dotenv()

client = API(access_token=os.getenv("OANDA_API_KEY"))

def fetch_pair(pair, granularity="M5",count=5000):
    r = instruments.InstrumentsCandles(instrument=pair,params={
    "granularity":granularity,
    "count":count,
    "price":"M"})
    try:
        client.request(r)
    except Exception as e:
        print(f"Failed to fetch{pair} : {e}")
    candles = r.response["candles"]
    data=[{
        "time":c["time"],
        "open":float(c["mid"]["o"]),
        "high":float(c["mid"]["h"]),
        "low":float(c["mid"]["l"]),
        "close":float(c["mid"]["c"]),
        "volume":float(c["volume"])

    } for c in candles if c["complete"]]

    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"],utc = True)
    os.makedirs("data", exist_ok=True)
    df.to_csv(f"data/{pair}.csv", index=False)
    print(f" Saved data/{pair}.csv")

    return df

if __name__ == "__main__":
    for p in[ "XAU_USD", "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]:
        fetch_pair(p)