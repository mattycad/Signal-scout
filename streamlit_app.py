import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import concurrent.futures
from datetime import datetime

st.set_page_config(page_title="📈 Signal Scout: Stocks, Crypto, Commodities & Forex", layout="centered")
st.title("📈 Signal Scout: Stocks, Crypto, Commodities & Forex")
st.write("Analyze multiple asset classes with Buy/Sell/Hold signals and alerts on changes.")

# Asset list (add more as you want)
assets = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Amazon (AMZN)": "AMZN",
    "Tesla (TSLA)": "TSLA",
    "NVIDIA (NVDA)": "NVDA",
    "Bitcoin (BTC-USD)": "BTC-USD",
    "Ethereum (ETH-USD)": "ETH-USD",
    "Binance Coin (BNB-USD)": "BNB-USD",
    "Cardano (ADA-USD)": "ADA-USD",
    "Solana (SOL-USD)": "SOL-USD",
    "Gold (GC=F)": "GC=F",
    "Silver (SI=F)": "SI=F",
    "Crude Oil WTI (CL=F)": "CL=F",
    "Brent Oil (BZ=F)": "BZ=F",
    "Natural Gas (NG=F)": "NG=F",
    "Copper (HG=F)": "HG=F",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "NZD/USD": "NZDUSD=X",
    "USD/CAD": "USDCAD=X",
    "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X"
}

# Cache data loading for 1 hour
@st.cache_data(ttl=3600)
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    df.dropna(inplace=True)
    return df

def compute_signal(df):
    if 'Close' not in df.columns:
        return "HOLD", "No Close price data", None

    close = df['Close'].dropna()

    # Check for enough data points
    if close.empty or len(close) < 21:
        return "HOLD", "Insufficient Close price data", None

    try:
        rsi = ta.momentum.RSIIndicator(close).rsi()
        sma20 = ta.trend.SMAIndicator(close, 20).sma_indicator()
        macd = ta.trend.MACD(close)
        macd_line = macd.macd()
        macd_signal = macd.macd_signal()

        # Drop NaNs to get latest valid values
        rsi_val = rsi.dropna().iloc[-1]
        sma_val = sma20.dropna().iloc[-1]
        macd_val = macd_line.dropna().iloc[-1]
        macd_sig_val = macd_signal.dropna().iloc[-1]
        price = close.iloc[-1]

        if rsi_val < 30 and price > sma_val and macd_val > macd_sig_val:
            return "BUY", "RSI < 30, Price > SMA20, MACD bullish crossover", price
        elif rsi_val > 70 and price < sma_val and macd_val < macd_sig_val:
            return "SELL", "RSI > 70, Price < SMA20, MACD bearish crossover", price
        else:
            return "HOLD", "No clear signal", price

    except Exception as e:
        return "HOLD", f"Indicator calculation error: {e}", None

# Session state for alerts
if 'prev_buy' not in st.session_state:
    st.session_state.prev_buy = set()
if 'prev_sell' not in st.session_state:
    st.session_state.prev_sell = set()

st.subheader("🚀 Asset Signals")

def scan_asset(name, ticker):
    try:
        df = get_data(ticker)
        signal, reason, price = compute_signal(df)
        return (name, signal, reason, price)
    except Exception as e:
        return (name, "HOLD", f"Error loading data: {e}", None)

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(lambda item: scan_asset(*item), assets.items()))

buys = [(n, r, p) for n, s, r, p in results if s == "BUY"]
sells = [(n, r, p) for n, s, r, p in results if s == "SELL"]
holds = [(n, r, p) for n, s, r, p in results if s == "HOLD"]

def alert_changes(new_list, old_set, label):
    new_set = set(name for name, _, _ in new_list)
    added = new_set - old_set
    removed = old_set - new_set

    for name in added:
        st.success(f"🔔 New {label} Signal: {name}")
    for name in removed:
        st.warning(f"💡 Consider Closing: {name} is no longer a {label} signal")

    return new_set

st.write("🟢 Buy Signals:")
if buys:
    st.session_state.prev_buy = alert_changes(buys, st.session_state.prev_buy, "BUY")
    for name, reason, price in buys:
        st.write(f"🟢 {name} — ${price:.2f} — {reason}")
else:
    st.write("No BUY signals.")

st.write("🔴 Sell Signals:")
if sells:
    st.session_state.prev_sell = alert_changes(sells, st.session_state.prev_sell, "SELL")
    for name, reason, price in sells:
        st.write(f"🔴 {name} — ${price:.2f} — {reason}")
else:
    st.write("No SELL signals.")

st.write("🟡 Hold Signals:")
for name, reason, price in holds:
    price_str = f"${price:.2f}" if price else "N/A"
    st.write(f"🟡 {name}: {price_str} — {reason}")

st.markdown(f"---\nLast update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
