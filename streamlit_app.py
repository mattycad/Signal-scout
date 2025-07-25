import streamlit as st
import yfinance as yf
import ta

st.set_page_config(page_title="📈 Signal Scout UK", layout="centered")
st.title("📈 Signal Scout UK")
st.write("Analyze real-time UK stocks, crypto, and commodities with Buy/Sell/Hold signals.")

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
    "Gold (GC=F)": "GC=F",
    "Silver (SI=F)": "SI=F",
    "Crude Oil WTI (CL=F)": "CL=F",
}

selected_asset = st.selectbox("Choose a stock, crypto, or commodity:", list(assets.keys()))
ticker = assets[selected_asset]

logic_mode = st.selectbox("Select Logic Mode", ["Simple", "Combined"])

@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    df.dropna(inplace=True)
    return df

try:
    df = get_data(ticker)

    # Make sure Close is a Series, not DataFrame slice
    close = df["Close"].squeeze()
    if close.ndim != 1:
        close = close.iloc[:,0]

    # Calculate indicators with 1D series input, outputs are also 1D
    rsi = ta.momentum.RSIIndicator(close).rsi()
    sma20 = ta.trend.SMAIndicator(close, window=20).sma_indicator()
    macd_obj = ta.trend.MACD(close)
    macd = macd_obj.macd()
    macd_signal = macd_obj.macd_signal()

    # Assign back to df for plotting or further usage if needed
    df["RSI"] = rsi
    df["SMA_20"] = sma20
    df["MACD"] = macd
    df["MACD_Signal"] = macd_signal

    latest = df.iloc[-1]

    # Extract scalar float values explicitly to avoid ambiguous truth errors
    rsi_val = float(latest["RSI"])
    close_val = float(latest["Close"])
    sma_val = float(latest["SMA_20"])
    macd_val = float(latest["MACD"])
    macd_signal_val = float(latest["MACD_Signal"])

    signal = "HOLD"
    reason = ""

    if logic_mode == "Simple":
        if rsi_val < 30:
            signal = "BUY"
            reason = "RSI < 30 (Oversold)"
        elif rsi_val > 70:
            signal = "SELL"
            reason = "RSI > 70 (Overbought)"
    else:
        if (rsi_val < 30) and (close_val > sma_val) and (macd_val > macd_signal_val):
            signal = "BUY"
            reason = "RSI < 30 + Price > SMA + MACD crossover"
        elif (rsi_val > 70) and (close_val < sma_val) and (macd_val < macd_signal_val):
            signal = "SELL"
            reason = "RSI > 70 + Price < SMA + MACD cross down"

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
