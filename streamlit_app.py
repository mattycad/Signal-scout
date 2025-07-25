import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# === CONFIG ===
st.set_page_config(page_title="Signal Scout", layout="centered")

st.title("📈 Signal Scout")
st.write("✅ App started loading...")
st.write("Get Buy/Sell/Hold signals for stocks & crypto based on technical indicators.")

# === INPUTS ===
ticker = st.text_input("Enter Ticker Symbol (e.g., AAPL or BTC-USD)", "AAPL")
logic_mode = st.selectbox("Select Logic Mode", ["Simple", "Combined"])

st.markdown("---")

# === HELPER FUNCTION ===
@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d")
    df.dropna(inplace=True)
    return df

# === MAIN LOGIC ===
try:
    df = get_data(ticker)

    # === INDICATORS ===
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi().squeeze()
    df["SMA_20"] = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator().squeeze()
    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd().squeeze()
    df["MACD_Signal"] = macd.macd_signal().squeeze()

    latest = df.iloc[-1]

    # === SIGNAL LOGIC ===
    signal = "HOLD"
    reason = ""

    if logic_mode == "Simple":
        if latest["RSI"] < 30:
            signal = "BUY"
            reason = "RSI < 30 (oversold)"
        elif latest["RSI"] > 70:
            signal = "SELL"
            reason = "RSI > 70 (overbought)"
    else:  # Combined logic
        if (
            latest["RSI"] < 30 and
            latest["Close"] > latest["SMA_20"] and
            latest["MACD"] > latest["MACD_Signal"]
        ):
            signal = "BUY"
            reason = "RSI < 30 AND Price > SMA AND MACD crossover"
        elif (
            latest["RSI"] > 70 and
            latest["Close"] < latest["SMA_20"] and
            latest["MACD"] < latest["MACD_Signal"]
        ):
            signal = "SELL"
            reason = "RSI > 70 AND Price < SMA AND MACD cross down"

    # === DISPLAY OUTPUT ===
    st.subheader(f"{ticker.upper()} Analysis")
    st.write(f"📈 Latest Price: **${latest['Close']:.2f}**")
    st.write(f"📊 RSI: **{latest['RSI']:.2f}**")
    st.write(f"🟡 SMA (20): **{latest['SMA_20']:.2f}**")
    st.write(f"📉 MACD: **{latest['MACD']:.2f} | Signal: {latest['MACD_Signal']:.2f}**")

    st.markdown("---")
    color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
    st.markdown(f"### Signal: {color[signal]} **{signal}**")
    if reason:
        st.caption(f"🚀 Reason: {reason}")

except Exception as e:
    st.error(f"❌ Something went wrong: {e}")
