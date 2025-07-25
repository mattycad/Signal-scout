import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# === STREAMLIT SETUP ===
st.set_page_config(page_title="📈 Signal Scout UK", layout="centered")
st.title("📈 Signal Scout UK")
st.write("Analyze real-time UK stocks & crypto and get instant Buy/Sell/Hold signals.")

# === ASSET DROPDOWN ===
st.subheader("Select an Asset")

assets = {
    "AstraZeneca (AZN)": "AZN.L",
    "HSBC Holdings (HSBA)": "HSBA.L",
    "Shell (SHEL)": "SHEL.L",
    "BP (BP)": "BP.L",
    "Unilever (ULVR)": "ULVR.L",
    "Diageo (DGE)": "DGE.L",
    "Tesco (TSCO)": "TSCO.L",
    "GlaxoSmithKline (GSK)": "GSK.L",
    "Barclays (BARC)": "BARC.L",
    "Rolls-Royce (RR)": "RR.L",
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Cardano (ADA)": "ADA-USD",
    "Solana (SOL)": "SOL-USD",
    "Polygon (MATIC)": "MATIC-USD",
    "Polkadot (DOT)": "DOT-USD",
    "Ripple (XRP)": "XRP-USD",
    "Dogecoin (DOGE)": "DOGE-USD",
    "Litecoin (LTC)": "LTC-USD",
    "Chainlink (LINK)": "LINK-USD"
}

selected_asset = st.selectbox("Choose a stock or crypto:", list(assets.keys()))
ticker = assets[selected_asset]

logic_mode = st.selectbox("Select Logic Mode", ["Simple", "Combined"])

# === DATA FETCHING ===
@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    df.dropna(inplace=True)
    return df

try:
    df = get_data(ticker)

    # === TECHNICAL INDICATORS - fixed for 1D data ===
    df["RSI"] = pd.Series(ta.momentum.RSIIndicator(df["Close"]).rsi().values.flatten(), index=df.index)
    df["SMA_20"] = pd.Series(ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator().values.flatten(), index=df.index)
    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = pd.Series(macd.macd().values.flatten(), index=df.index)
    df["MACD_Signal"] = pd.Series(macd.macd_signal().values.flatten(), index=df.index)

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
    else:  # Combined
        if latest["RSI"] < 30 and latest["Close"] > latest["SMA_20"] and latest["MACD"] > latest["MACD_Signal"]:
            signal = "BUY"
            reason = "RSI < 30 + Price > SMA + MACD crossover"
        elif latest["RSI"] > 70 and latest["Close"] < latest["SMA_20"] and latest["MACD"] < latest["MACD_Signal"]:
            signal = "SELL"
            reason = "RSI > 70 + Price < SMA + MACD cross down"

    # === METRICS ===
    st.markdown("---")
    st.subheader(f"📊 {selected_asset} Technical Summary")
    st.metric("Latest Price", f"${latest['Close']:.2f}")
    st.write(f"📉 RSI: **{latest['RSI']:.2f}**")
    st.write(f"📈 SMA (20): **{latest['SMA_20']:.2f}**")
    st.write(f"📊 MACD: **{latest['MACD']:.2f}** | Signal: **{latest['MACD_Signal']:.2f}**")

    st.markdown("---")
    color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
    st.markdown(f"### Signal: {color[signal]} **{signal}**")
    if reason:
        st.caption(f"📌 Reason: {reason}")

except Exception as e:
    st.error(f"❌ Something went wrong while analyzing data: {e}")
