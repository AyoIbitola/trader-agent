

import os
import time
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv
import asyncio
import httpx
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
from streamlit_autorefresh import st_autorefresh

load_dotenv()


OANDA_API_KEY = os.getenv("OANDA_API_KEY")
BACKEND_URL = os.getenv("FAST_API_URL") or "http://localhost:8000"
DEFAULT_PAIR = "XAU_USD"
PAIRS = ["XAU_USD", "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]
PAIR_DISPLAY = {p: p.replace("_", "/") for p in PAIRS}
DEFAULT_GRANULARITY = "M5"
DEFAULT_COUNT = 200


oanda_client = None
if OANDA_API_KEY:
    try:
        oanda_client = API(access_token=OANDA_API_KEY)
    except Exception as e:
        oanda_client = None
        st.warning(f"OANDA client init failed: {e}")


if "last_fetch_time" not in st.session_state:
    st.session_state.last_fetch_time = "n/a"
if "last_backend" not in st.session_state:
    st.session_state.last_backend = 0.0



@st.cache_data(ttl=25, show_spinner=False)
def fetch_oanda_candles(pair: str, granularity: str = DEFAULT_GRANULARITY, count: int = DEFAULT_COUNT):
    if oanda_client is None:
        raise RuntimeError("OANDA_API_KEY not set or OANDA client failed to initialize.")
    
    try:
        r = instruments.InstrumentsCandles(
            instrument=pair,
            params={"granularity": granularity, "count": count, "price": "M"},
        )
        oanda_client.request(r)
        candles = r.response.get("candles", [])
    except Exception as e:
        raise RuntimeError(f"OANDA API request failed: {e}")
    
    rows = []
    for c in candles:
        if not c.get("complete", False):
            continue
        t = pd.to_datetime(c["time"])
        rows.append({
            "time": t.tz_convert(None) if hasattr(t, "tz_convert") else t,
            "open": float(c["mid"]["o"]),
            "high": float(c["mid"]["h"]),
            "low": float(c["mid"]["l"]),
            "close": float(c["mid"]["c"]),
            "volume": float(c.get("volume", 0)),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df.sort_values("time", inplace=True)
        df.reset_index(drop=True, inplace=True)
    return df

def plot_candlestick(df: pd.DataFrame, title: str):
    if df.empty:
        return None
    
    fig = go.Figure(data=[go.Candlestick(
        x=df["time"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing_line_color="green",
        decreasing_line_color="red",
    )])
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        margin=dict(l=12, r=12, t=36, b=12),
        height=520,
        title=title
    )
    return fig

async def backend_trigger_predict():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{BACKEND_URL}/predict")
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        return {"error": "Cannot connect to backend server"}
    except httpx.TimeoutException:
        return {"error": "Backend request timed out"}
    except Exception as e:
        return {"error": f"Backend error: {str(e)}"}

async def backend_get_history(limit=100):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{BACKEND_URL}/history", params={"limit": limit})
            resp.raise_for_status()
            return resp.json().get("history", [])
    except httpx.ConnectError:
        return {"error": "Cannot connect to backend server"}
    except httpx.TimeoutException:
        return {"error": "Backend request timed out"}
    except Exception as e:
        return {"error": f"Backend error: {str(e)}"}

def compute_kpis(df: pd.DataFrame):
    if df is None or df.empty:
        return None
    current = df.iloc[-1]["close"]
    last_24h = df.tail(288) if len(df) >= 288 else df
    high_24h = float(last_24h["high"].max())
    low_24h = float(last_24h["low"].min())
    first_close = float(last_24h.iloc[0]["close"]) if not last_24h.empty else current
    change_val = current - first_close
    change_pct = (change_val / first_close) if first_close != 0 else 0.0
    return {
        "current": float(current), 
        "change_val": float(change_val), 
        "change_pct": float(change_pct), 
        "high_24h": high_24h, 
        "low_24h": low_24h
    }


def run_async(func, *args, **kwargs):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, func(*args, **kwargs))
            return future.result()
    else:
        return loop.run_until_complete(func(*args, **kwargs))


st.set_page_config(page_title="AI Forex Signal Dashboard", layout="wide")
st.sidebar.title("⚙️ Controls")

pair = st.sidebar.selectbox("Pair", PAIRS, index=PAIRS.index(DEFAULT_PAIR))
pair_display = PAIR_DISPLAY.get(pair, pair.replace("_", "/"))

auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
refresh_interval = st.sidebar.selectbox("Interval (secs)", [10, 20, 30, 60, 120], index=2)

st.sidebar.markdown("---")
st.sidebar.caption("Candles: OANDA | Predictions: backend")
last_update_placeholder = st.sidebar.empty()

if auto_refresh:
    st_autorefresh(interval=refresh_interval * 1000, key=f"autorefresh_{pair}")


candles_error = None
candles_df = pd.DataFrame()
try:
    candles_df = fetch_oanda_candles(pair, granularity=DEFAULT_GRANULARITY, count=DEFAULT_COUNT)
    st.session_state.last_fetch_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
except Exception as e:
    candles_error = str(e)
    st.session_state.last_fetch_time = "n/a"

last_update_placeholder.markdown(f"⏱️ **Last updated:** `{st.session_state.last_fetch_time}`")


tabs = st.tabs(["Live Charts", "Latest Signals", "Signal History"])


with tabs[0]:
    st.markdown(f"## 📈 {pair_display} — Live Candlestick")
    if candles_error:
        st.error(f"Could not fetch candles: {candles_error}")
        st.info("Ensure OANDA_API_KEY is set and network access is available.")
    else:
        if candles_df.empty:
            st.warning("No candle data returned from OANDA.")
        else:
            col_chart, col_kpi = st.columns([3, 1], gap="large")
            with col_chart:
                fig = plot_candlestick(candles_df, f"{pair_display} — Live")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Could not generate chart")
            
            with col_kpi:
                kpis = compute_kpis(candles_df)
                if kpis:
                    st.markdown("### Market Snapshot")
                    price_format = f"${kpis['current']:.2f}" if pair == "XAU_USD" else f"${kpis['current']:.4f}"
                    st.metric("Current Price", price_format)
                    
                    val = kpis["change_val"]
                    pct = kpis["change_pct"]
                    sign = "+" if val >= 0 else ""
                    color = "green" if val >= 0 else "red"
                    
                    val_format = f"{val:.2f}" if pair == "XAU_USD" else f"{val:.4f}"
                    st.markdown(f"**24h Change**  \n<span style='color:{color};font-weight:600'>{sign}${val_format} ({sign}{pct:.2%})</span>", unsafe_allow_html=True)
                    
                    high_format = f"${kpis['high_24h']:.2f}" if pair == "XAU_USD" else f"${kpis['high_24h']:.4f}"
                    low_format = f"${kpis['low_24h']:.2f}" if pair == "XAU_USD" else f"${kpis['low_24h']:.4f}"
                    
                    st.markdown(f"**24h High**  \n{high_format}")
                    st.markdown(f"**24h Low**  \n{low_format}")
                else:
                    st.write("KPIs unavailable")

            bcol1, bcol2, bcol3 = st.columns(3)
            with bcol1:
                if st.button("Refresh Now"):
                    fetch_oanda_candles.clear()
                    st.rerun()  
            with bcol2:
                if st.button("Run Prediction (backend)"):
                    with st.spinner("Triggering backend prediction..."):
                        resp = run_async(backend_trigger_predict)
                    if resp.get("error"):
                        st.error(f"Prediction trigger error: {resp['error']}")
                    else:
                        st.success(resp.get("message", "Prediction triggered"))
            with bcol3:
                st.write("")


with tabs[1]:
    st.markdown("## 🔔 Latest Signals")

    backend_pred = None
   
    try:
        fetch_new = False
        current_time = time.time()
        time_since_last = current_time - st.session_state.last_backend
        
        if auto_refresh and time_since_last > max(60, refresh_interval):
            fetch_new = True

        if fetch_new:
            st.session_state.last_backend = current_time
            with st.spinner("Fetching latest predictions..."):
                backend_pred = run_async(backend_get_history)

        if st.button("Force Refresh Signals"):
            with st.spinner("Forcing fetch of latest signals..."):
                backend_pred = run_async(backend_get_history)
                st.session_state.last_backend = time.time()

        if backend_pred is None:
            st.info("Press `Force Refresh Signals` to load predictions (or wait for auto-refresh).")
        else:
            if isinstance(backend_pred, dict) and backend_pred.get("error"):
                st.error(f"Error fetching signals: {backend_pred['error']}")
            else:
                preds = backend_pred if isinstance(backend_pred, list) else backend_pred.get("predictions", [])
                if preds:
                    dfp = pd.DataFrame(preds)
                    if "pair" in dfp.columns:
                        dfp["pair"] = dfp["pair"].astype(str).str.replace("_", "/")
                    if "confidence" in dfp.columns:
                        dfp["confidence"] = dfp["confidence"].apply(
                            lambda x: f"{float(x):.2%}" if pd.notnull(x) and str(x).replace('.', '').isdigit() else str(x)
                        )
                    
                    
                    rename_cols = {}
                    if "pair" in dfp.columns:
                        rename_cols["pair"] = "Pair"
                    if "signal" in dfp.columns:
                        rename_cols["signal"] = "Signal"
                    if "predicted_price" in dfp.columns:
                        rename_cols["predicted_price"] = "Predicted Price"
                    
                    st.dataframe(dfp.rename(columns=rename_cols))
                else:
                    st.info("No predictions returned.")
    except Exception as e:
        st.error(f"Error fetching predictions: {e}")


with tabs[2]:
    st.markdown("## 📜 Signal History")
    try:
        with st.spinner("Fetching signal history..."):
            hist = run_async(backend_get_history, 200)
        
        if isinstance(hist, dict) and hist.get("error"):
            st.error(f"History fetch error: {hist['error']}")
        else:
            if isinstance(hist, list) and hist:
                hdf = pd.DataFrame(hist)
                
                
                if "timestamp" in hdf.columns:
                    try:
                        hdf["time"] = pd.to_datetime(hdf["timestamp"], unit="s", errors='coerce')
                    except Exception:
                        try:
                            hdf["time"] = pd.to_datetime(hdf["timestamp"], errors='coerce')
                        except Exception:
                            hdf["time"] = hdf["timestamp"]
                
                
                if "pair" in hdf.columns:
                    hdf["pair"] = hdf["pair"].astype(str).str.replace("_", "/")
                
                
                if "time" in hdf.columns:
                    hdf_sorted = hdf.sort_values(by="time", ascending=False)
                else:
                    hdf_sorted = hdf
                
                st.dataframe(hdf_sorted.head(300), use_container_width=True)
            else:
                st.info("No history yet.")
    except Exception as e:
        st.error(f"Error fetching history: {e}")


st.markdown("---")
