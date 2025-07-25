import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta

st.set_page_config(page_title="📈 Signal Scout Global", layout="centered")
st.title("📈 Signal Scout Global")
st.write("Analyze real-time stocks, crypto & commodities worldwide with Buy/Sell/Hold signals.")

# Expanded assets dictionary including UK, Global, Crypto, Commodities
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

    # US Stocks
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Amazon (AMZN)": "AMZN",
    "Alphabet (GOOGL)": "GOOGL",
    "Tesla (TSLA)": "TSLA",
    "Meta Platforms (META)": "META",
    "NVIDIA (NVDA)": "NVDA",
    "Johnson & Johnson (JNJ)": "JNJ",
    "JPMorgan Chase (JPM)": "JPM",
    "Visa (V)": "V",

    # European Stocks
    "Siemens (SIE.DE)": "SIE.DE",
    "SAP (SAP.DE)": "SAP.DE",
    "Volkswagen (VOW3.DE)": "VOW3.DE",
    "TotalEnergies (TTE.PA)": "TTE.PA",
    "L'Oréal (OR.PA)": "OR.PA",

    # Japanese Stocks
    "Toyota Motor (7203.T)": "7203.T",
    "Sony Group (6758.T)": "6758.T",
    "SoftBank Group (9984.T)": "9984.T",

    # Cryptocurrencies
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
    "Palladium (PA=F)": "PA=F",
    "Corn (ZC=F)": "ZC=F",
    "Soybean (ZS=F)": "ZS=F",
    "Wheat (ZW=F)": "ZW=F",
}

selected_asset = st.selectbox("Choose a stock, crypto, or commodity:", list(assets.keys()))
ticker = assets[selected_asset]

logic_mode = st.selectbox("Select Logic Mode", ["Simple", "Combined"])

@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    df.dropna(inplace=True)
    if isinstance(df["Close"], pd.DataFrame):
        df["Close"] = df["Close"].iloc[:, 0]
    return df

try:
    df = get_data(ticker)

    close_np = np.array(df["Close"]).flatten()
    close_series = pd.Series(close_np, index=df.index)

    rsi = ta.momentum.RSIIndicator(close_series).rsi()
    sma_20 = ta.trend.SMAIndicator(close_series, window=20).sma_indicator()
    macd_obj = ta.trend.MACD(close_series)
    macd = macd_obj.macd()
    macd_signal = macd_obj.macd_signal()

    df["RSI"] = rsi
    df["SMA_20"] = sma_20
    df["MACD"] = macd
    df["MACD_Signal"] = macd_signal

    df.dropna(inplace=True)

    latest = df.iloc[-1]

    signal = "HOLD"
    reason = ""

    if logic_mode == "Simple":
        if latest["RSI"] < 30:
            signal = "BUY"
            reason = "RSI < 30 (Oversold)"
        elif latest["RSI"] > 70:
            signal = "SELL"
            reason = "RSI > 70 (Overbought)"
    else:
        if latest["RSI"] < 30 and latest["Close"] > latest["SMA_20"] and latest["MACD"] > latest["MACD_Signal"]:
            signal = "BUY"
            reason = "RSI < 30 + Price > SMA + MACD crossover"
        elif latest["RSI"] > 70 and latest["Close"] < latest["SMA_20"] and latest["MACD"] < latest["MACD_Signal"]:
            signal = "SELL"
            reason = "RSI > 70 + Price < SMA + MACD cross down"

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

    st.markdown("### 📈 Price Chart (Last 3 Months)")
    st.line_chart(df["Close"])

    with st.expander("📉 Show RSI Chart"):
        st.line_chart(df["RSI"])

except Exception as e:
    st.error(f"❌ Something went wrong while analyzing data: {e}")
