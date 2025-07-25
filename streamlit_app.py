import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.set_page_config(page_title="📈 Signal Scout: Stocks, Crypto, Commodities & Forex", layout="wide")

st.title("📈 Signal Scout: Stocks, Crypto, Commodities & Forex")
st.markdown("Analyze multiple asset classes with Buy/Sell signals and alerts on changes.")

# Asset list (add more symbols as you want)
ASSETS = {
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
    "USD/CAD": "CAD=X",
    "USD/CHF": "CHF=X",
    "AUD/USD": "AUDUSD=X",
}

@st.cache_data(ttl=3600)
def fetch_data(ticker):
    # Fetch 90 days history (1 day interval)
    try:
        df = yf.download(ticker, period="90d", interval="1d", progress=False)
        if df.empty:
            return None
        return df
    except Exception:
        return None

def compute_signal(df):
    if df is None or 'Close' not in df.columns:
        return "HOLD", "No Close price data", None

    close = df['Close']
    # Ensure 1D Series (fix error)
    if isinstance(close, pd.DataFrame):
        close = close.squeeze()
    close = close.dropna()
    if close.empty or len(close) < 21:
        return "HOLD", "Insufficient Close price data", None

    try:
        rsi = ta.momentum.RSIIndicator(close).rsi()
        sma20 = ta.trend.SMAIndicator(close, 20).sma_indicator()
        macd = ta.trend.MACD(close)
        macd_line = macd.macd()
        macd_signal = macd.macd_signal()

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

# For alerting changes between runs (stored in session_state)
if "prev_buy" not in st.session_state:
    st.session_state.prev_buy = set()
if "prev_sell" not in st.session_state:
    st.session_state.prev_sell = set()

def alert_changes(current_signals, prev_signals, signal_type):
    current_names = set([name for name, _, _ in current_signals])
    added = current_names - prev_signals
    removed = prev_signals - current_names

    for name in added:
        st.balloons()
        st.toast(f"🔔 New {signal_type}: {name}")

    return current_names

results = []

with st.spinner("Fetching and analyzing data..."):
    for name, ticker in ASSETS.items():
        df = fetch_data(ticker)
        signal, reason, price = compute_signal(df)
        results.append((name, signal, reason, price))

# Separate BUY and SELL signals; ignore HOLD from display
buys = [(n, r, p) for n, s, r, p in results if s == "BUY"]
sells = [(n, r, p) for n, s, r, p in results if s == "SELL"]

st.subheader("🚀 Asset Signals")

st.markdown("### 🟢 Buy Signals")
if buys:
    st.session_state.prev_buy = alert_changes(buys, st.session_state.prev_buy, "BUY")
    for name, reason, price in buys:
        st.write(f"🟢 **{name}** — ${price:.2f} — {reason}")
else:
    st.write("No BUY signals.")

st.markdown("### 🔴 Sell Signals")
if sells:
    st.session_state.prev_sell = alert_changes(sells, st.session_state.prev_sell, "SELL")
    for name, reason, price in sells:
        st.write(f"🔴 **{name}** — ${price:.2f} — {reason}")
else:
    st.write("No SELL signals.")

st.markdown(f"Last update: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
