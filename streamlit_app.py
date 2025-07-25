import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

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
    "---": "---",
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

filtered_assets = {k: v for k, v in assets.items() if v != "---"}
selected_asset = st.selectbox("Choose a stock or crypto:", list(filtered_assets.keys()))
ticker = filtered_assets[selected_asset]

logic_mode = st.selectbox("Select Logic Mode", ["Simple", "Combined"])

# === DATA FETCHING ===
@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    df.dropna(inplace=True)
    return df

try:
    df = get_data(ticker)

    # === TECHNICAL INDICATORS (Fixed 1D using .squeeze()) ===
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

    # === PLOTLY CANDLESTICK CHART ===
    st.markdown("### 📈 Price Chart (Last 3 Months)")

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["SMA_20"],
        mode='lines',
        line=dict(color='orange', width=1.5),
        name='SMA 20'
    ))

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        title=f"{selected_asset} Candlestick Chart"
    )

    st.plotly_chart(fig, use_container_width=True)

    # === RSI CHART ===
    with st.expander("📉 Show RSI Chart"):
        rsi_fig = go.Figure()
        rsi_fig.add_trace(go.Scatter(
            x=df.index,
            y=df["RSI"],
            mode='lines',
            line=dict(color='purple'),
            name='RSI'
        ))
        rsi_fig.update_layout(height=300, title="RSI (Relative Strength Index)", yaxis=dict(range=[0, 100]))
        st.plotly_chart(rsi_fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ Something went wrong while analyzing data: {e}")
