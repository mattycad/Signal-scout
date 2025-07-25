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

    # === TECHNICAL INDICATORS ===
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    df["SMA_20"] = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator()
    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()

    latest = df.iloc[-1]

    # === SIGNAL LOGIC ===
    signal = "HOLD"
    reason = ""

    if logic_mode == "Simple":
        if latest["RSI"] < 30:
            signal = "BUY"
            reason = "RSI < 30 (Oversold)"
        elif latest["RSI"] > 70:
            signal = "SELL"
            reason = "RSI > 70 (Overbought)"
    else:  # Combined logic
        if (
            latest["RSI"] < 30 and
            latest["Close"] > latest["SMA_20"] and
            latest["MACD"] > latest["MACD_Signal"]
        ):
            signal = "BUY"
            reason = "RSI < 30 + Price > SMA + MACD crossover"
        elif (
            latest["RSI"] > 70 and
            latest["Close"] < latest["SMA_20"] and
            latest["MACD"] < latest["MACD_Signal"]
        ):
            signal = "SELL"
            reason = "RSI > 70 + Price < SMA + MACD cross down"

    # === DISPLAY ===
    st.subheader(f"{ticker.upper()} Analysis")
    st.metric("Latest Price", f"${latest['Close']:.2f}")
    st.write(f"📊 RSI: **{latest['RSI']:.2f}**")
    st.write(f"📈 SMA (20): **{latest['SMA_20']:.2f}**")
    st.write(f"📉 MACD: **{latest['MACD']:.2f}** | Signal: **{latest['MACD_Signal']:.2f}**")

    st.markdown("---")
    color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
    st.markdown(f"### Signal: {color[signal]} **{signal}**")
    if reason:
        st.caption(f"📌 Reason: {reason}")

except Exception as e:
    st.error(f"Something went wrong: {e}")
