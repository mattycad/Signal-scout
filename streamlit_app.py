import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# === PAGE SETUP ===
st.set_page_config(page_title="📈 Signal Scout UK", layout="centered")
st.title("📈 Signal Scout UK")
st.write("Get real-time **Buy/Sell/Hold** signals for UK stocks and cryptocurrencies.")

# === BEGINNER-FRIENDLY ASSET LIST ===
st.subheader("🔍 Select a Stock or Crypto")

assets = {
    "📈 FTSE 100 Stocks": {
        "AstraZeneca (AZN)": "AZN.L",
        "HSBC Holdings (HSBA)": "HSBA.L",
        "Shell (SHEL)": "SHEL.L",
        "Unilever (ULVR)": "ULVR.L",
        "BP (BP)": "BP.L",
        "Diageo (DGE)": "DGE.L",
        "Barclays (BARC)": "BARC.L",
        "Rolls-Royce (RR)": "RR.L",
        "Tesco (TSCO)": "TSCO.L",
        "GlaxoSmithKline (GSK)": "GSK.L"
    },
    "📊 FTSE 250 / AIM Stocks": {
        "Marks & Spencer (MKS)": "MKS.L",
        "easyJet (EZJ)": "EZJ.L",
        "Wizz Air (WIZZ)": "WIZZ.L",
        "AO World (AO)": "AO.L",
        "Fevertree Drinks (FEVR)": "FEVR.L"
    },
    "💱 Cryptocurrencies": {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Cardano (ADA)": "ADA-USD",
        "Solana (SOL)": "SOL-USD",
        "Polygon (MATIC)": "MATIC-USD",
        "Polkadot (DOT)": "DOT-USD",
        "Ripple (XRP)": "XRP-USD",
        "Dogecoin (DOGE)": "DOGE-USD",
        "Litecoin (LTC)": "LTC-USD"
    }
}

# Flatten the grouped options for Streamlit selectbox
grouped_options = []
ticker_map = {}
for group, items in assets.items():
    grouped_options.append(f"--- {group} ---")
    for name, ticker_code in items.items():
        grouped_options.append(name)
        ticker_map[name] = ticker_code

selected_asset = st.selectbox("Choose from the list below:", grouped_options)
if selected_asset.startswith("---"):
    st.info("Please select an actual stock or crypto.")
    st.stop()

ticker = ticker_map[selected_asset]

# === LOGIC SELECTION ===
logic_mode = st.radio("Signal Logic Mode", ["Simple", "Combined"], horizontal=True)

# === FETCH PRICE DATA ===
@st.cache_data(ttl=300)
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
    else:  # Combined
        if latest["RSI"] < 30 and latest["Close"] > latest["SMA_20"] and latest["MACD"] > latest["MACD_Signal"]:
            signal = "BUY"
            reason = "RSI < 30 + Price > SMA + MACD crossover"
        elif latest["RSI"] > 70 and latest["Close"] < latest["SMA_20"] and latest["MACD"] < latest["MACD_Signal"]:
            signal = "SELL"
            reason = "RSI > 70 + Price < SMA + MACD cross down"

    # === DISPLAY ===
    st.markdown("---")
    st.subheader(f"📊 {selected_asset} Technical Summary")
    st.metric("💵 Latest Price", f"${latest['Close']:.2f}")
    st.write(f"📉 RSI: **{latest['RSI']:.2f}**")
    st.write(f"📈 SMA (20): **{latest['SMA_20']:.2f}**")
    st.write(f"📊 MACD: **{latest['MACD']:.2f}** vs Signal: **{latest['MACD_Signal']:.2f}**")

    st.markdown("---")
    colors = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
    st.markdown(f"### 📌 Final Signal: {colors[signal]} **{signal}**")
    if reason:
        st.caption(f"🧠 Logic Reason: {reason}")

except Exception as e:
    st.error(f"Something went wrong while analyzing data: {e}")
