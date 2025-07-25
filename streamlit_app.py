import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# === STREAMLIT SETUP ===
st.set_page_config(page_title="📈 Signal Scout UK", layout="centered")
st.title("📈 Signal Scout UK")
st.write("Analyze real-time UK stocks, crypto, and commodities with Buy/Sell/Hold signals.")

# === ASSET DROPDOWN ===
st.subheader("Select an Asset")

assets = {
    # UK Stocks
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
    # Crypto
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Cardano (ADA)": "ADA-USD",
    "Solana (SOL)": "SOL-USD",
    "Polygon (MATIC)": "MATIC-USD",
    "Polkadot (DOT)": "DOT-USD",
    "Ripple (XRP)": "XRP-USD",
    "Dogecoin (DOGE)": "DOGE-USD",
    "Litecoin (LTC)": "LTC-USD",
    "Chainlink (LINK)": "LINK-USD",
    # Commodities
    "Gold (GC=F)": "GC=F",
    "Silver (SI=F)": "SI=F",
    "Crude Oil WTI (CL=F)": "CL=F",
    "Natural Gas (NG=F)": "NG=F",
    "Copper (HG=F)": "HG=F",
    "Platinum (PL=F)": "PL=F",
}

selected_asset = st.selectbox("Choose a stock, crypto, or commodity:", list(assets.keys()))
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

    # === TECHNICAL INDICATORS ===
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi().squeeze()
    df["SMA_20"] = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator().squeeze()
    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd().squeeze()
    df["MACD_Signal"] = macd.macd_signal().squeeze()

    latest = df.iloc[-1]

    # Convert to float to avoid ambiguous Series error
    rsi_val = float(latest["RSI"])
    close_val = float(latest["Close"])
    sma_val = float(latest["SMA_20"])
    macd_val = float(latest["MACD"])
    macd_signal_val = float(latest["MACD_Signal"])

    # === SIGNAL LOGIC ===
    signal = "HOLD"
    reason = ""

    if logic_mode == "Simple":
        if rsi_val < 30:
            signal = "BUY"
            reason = "RSI < 30 (Oversold)"
        elif rsi_val > 70:
            signal = "SELL"
            reason = "RSI > 70 (Overbought)"
    else:  # Combined
        if (rsi_val < 30) and (close_val > sma_val) and (macd_val > macd_signal_val):
            signal = "BUY"
            reason = "RSI < 30 + Price > SMA + MACD crossover"
        elif (rsi_val > 70) and (close_val < sma_val) and (macd_val < macd_signal_val):
            signal = "SELL"
            reason = "RSI > 70 + Price < SMA + MACD cross down"

    # === METRICS ===
    st.markdown("---")
    st.subheader(f"📊 {selected_asset} Technical Summary")
    st.metric("Latest Price", f"${close_val:.2f}")
    st.write(f"📉 RSI: **{rsi_val:.2f}**")
    st.write(f"📈 SMA (20): **{sma_val:.2f}**")
    st.write(f"📊 MACD: **{macd_val:.2f}** | Signal: **{macd_signal_val:.2f}**")

    st.markdown("---")
    color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
    st.markdown(f"### Signal: {color[signal]} **{signal}**")
    if reason:
        st.caption(f"📌 Reason: {reason}")

except Exception as e:
    st.error(f"❌ Something went wrong while analyzing data: {e}")
