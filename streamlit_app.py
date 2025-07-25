import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# === SETUP ===
st.set_page_config(page_title="📈 Real-Time Signal Scout", layout="centered")
st.title("📈 Real-Time Signal Scout")
st.write("Analyze real-time stock & crypto prices and get instant Buy/Sell/Hold signals.")

# === USER INPUT ===
ticker = st.text_input("Enter Ticker Symbol (e.g., AAPL or BTC-USD)", "AAPL")
logic_mode = st.selectbox("Select Logic Mode", ["Simple", "Combined"])

# === DATA FETCH ===
@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    df.dropna(inplace=True)
    return df

try:
    df = get_data(ticker)

    # Ensure Close column is 1D Series for ta
    close_series = df["Close"].squeeze()

    # === TECHNICAL INDICATORS ===
    df["RSI"] = ta.momentum.RSIIndicator(close_series).rsi()
    df["SMA_20"] = ta.trend.SMAIndicator(close_series, window=20).sma_indicator()
    macd = ta.trend.MACD(close_series)
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()

    latest = df.iloc[-1]

    # Cast values to float scalars to avoid ambiguous truth value errors
    rsi = float(latest["RSI"])
    close = float(latest["Close"])
    sma_20 = float(latest["SMA_20"])
    macd_val = float(latest["MACD"])
    macd_signal = float(latest["MACD_Signal"])

    # === SIGNAL LOGIC ===
    signal = "HOLD"
    reason = ""

    if logic_mode == "Simple":
        if rsi < 30:
            signal = "BUY"
            reason = "RSI < 30 (Oversold)"
        elif rsi > 70:
            signal = "SELL"
            reason = "RSI > 70 (Overbought)"
    else:  # Combined logic
        if rsi < 30 and close > sma_20 and macd_val > macd_signal:
            signal = "BUY"
            reason = "RSI < 30 + Price > SMA + MACD crossover"
        elif rsi > 70 and close < sma_20 and macd_val < macd_signal:
            signal = "SELL"
            reason = "RSI > 70 + Price < SMA + MACD cross down"

    # === DISPLAY ===
    st.subheader(f"{ticker.upper()} Analysis")
    st.metric("Latest Price", f"${close:.2f}")
    st.write(f"📊 RSI: **{rsi:.2f}**")
    st.write(f"📈 SMA (20): **{sma_20:.2f}**")
    st.write(f"📉 MACD: **{macd_val:.2f}** | Signal: **{macd_signal:.2f}**")

    st.markdown("---")
    color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
    st.markdown(f"### Signal: {color[signal]} **{signal}**")
    if reason:
        st.caption(f"📌 Reason: {reason}")

except Exception as e:
    st.error(f"Something went wrong: {e}")
