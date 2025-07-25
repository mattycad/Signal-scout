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

def calculate_signal(df, logic_mode):
    close = df["Close"].squeeze()
    if close.ndim != 1:
        close = close.iloc[:,0]

    rsi = ta.momentum.RSIIndicator(close).rsi()
    sma20 = ta.trend.SMAIndicator(close, window=20).sma_indicator()
    macd_obj = ta.trend.MACD(close)
    macd = macd_obj.macd()
    macd_signal = macd_obj.macd_signal()

    latest = df.iloc[-1]

    rsi_val = float(latest["RSI"]) if "RSI" in df.columns else float(rsi.iloc[-1])
    sma_val = float(latest["SMA_20"]) if "SMA_20" in df.columns else float(sma20.iloc[-1])
    macd_val = float(latest["MACD"]) if "MACD" in df.columns else float(macd.iloc[-1])
    macd_signal_val = float(latest["MACD_Signal"]) if "MACD_Signal" in df.columns else float(macd_signal.iloc[-1])
    close_val = float(latest["Close"])

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

    return signal, reason, rsi_val, sma_val, macd_val, macd_signal_val, close_val

try:
    # Analyze selected asset
    df = get_data(ticker)
    signal, reason, rsi_val, sma_val, macd_val, macd_signal_val, close_val = calculate_signal(df, logic_mode)

    st.markdown("---")
    st.subheader(f"📊 {selected_asset} Technical Summary")
    st.metric("Latest Price", f"${close_val:.2f}")
    st.write(f"📉 RSI: **{rsi_val:.2f}**")
    st.write(f"📈 SMA (20): **{sma_val:.2f}**")
    st.write(f"📊 MACD: **{macd_val:.2f}** | Signal: **{macd_signal_val:.2f}**")

    color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
    st.markdown(f"### Signal: {color[signal]} **{signal}**")
    if reason:
        st.caption(f"📌 Reason: {reason}")

    # Scan all assets for BUY and SELL signals
    st.markdown("---")
    st.subheader("🚀 Best Assets to Buy Now")

    best_buys = []
    best_sells = []
    for name, sym in assets.items():
        try:
            data = get_data(sym)
            sig, _, _, _, _, _, price = calculate_signal(data, logic_mode)
            if sig == "BUY":
                best_buys.append((name, price))
            elif sig == "SELL":
                best_sells.append((name, price))
        except Exception:
            continue  # skip if data fails

    if best_buys:
        for asset_name, price in best_buys:
            st.write(f"🟢 **{asset_name}** at ${price:.2f}")
    else:
        st.write("No BUY signals found right now.")

    st.markdown("---")
    st.subheader("⚠️ Best Assets to Sell Now")

    if best_sells:
        for asset_name, price in best_sells:
            st.write(f"🔴 **{asset_name}** at ${price:.2f}")
    else:
        st.write("No SELL signals found right now.")

except Exception as e:
    st.error(f"❌ Something went wrong while analyzing data: {e}")
