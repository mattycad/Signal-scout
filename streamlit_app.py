import streamlit as st
import yfinance as yf
import ta
import concurrent.futures
import plotly.graph_objs as go

st.set_page_config(page_title="📈 Signal Scout Global", layout="centered")
st.title("📈 Signal Scout Global")
st.write("Analyze real-time global stocks, crypto, commodities, and currencies with Buy/Sell/Hold signals.")

assets = {
    # Sample selection for brevity — use full list as before
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Gold (GC=F)": "GC=F",
    "EUR/USD": "EURUSD=X"
}

selected_asset = st.selectbox("Choose a stock, crypto, commodity, or currency:", list(assets.keys()))
ticker = assets[selected_asset]
logic_mode = st.selectbox("Select Logic Mode", ["Simple", "Combined"])

@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    df.dropna(inplace=True)
    return df

def calculate_signal(df, logic_mode):
    close = df["Close"]
    rsi = ta.momentum.RSIIndicator(close).rsi()
    sma = ta.trend.SMAIndicator(close, window=20).sma_indicator()
    macd_obj = ta.trend.MACD(close)
    macd = macd_obj.macd()
    macd_signal = macd_obj.macd_signal()

    rsi_val = float(rsi.iloc[-1])
    sma_val = float(sma.iloc[-1])
    macd_val = float(macd.iloc[-1])
    macd_signal_val = float(macd_signal.iloc[-1])
    close_val = float(close.iloc[-1])

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

# --- Store state for change alerts ---
if "prev_buy_assets" not in st.session_state:
    st.session_state.prev_buy_assets = []
if "prev_sell_assets" not in st.session_state:
    st.session_state.prev_sell_assets = []

# --- Selected Asset Analysis ---
try:
    df = get_data(ticker)
    signal, reason, rsi_val, sma_val, macd_val, macd_signal_val, close_val = calculate_signal(df, logic_mode)

    st.markdown("---")
    st.subheader(f"📊 {selected_asset} Technical Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Latest Price", f"${close_val:.2f}")
    col2.metric("RSI", f"{rsi_val:.2f}")
    col3.metric("SMA 20", f"{sma_val:.2f}")

    st.write(f"📊 MACD: **{macd_val:.2f}** | Signal Line: **{macd_signal_val:.2f}**")

    color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
    st.markdown(f"### Signal: {color[signal]} **{signal}**")
    if reason:
        st.caption(f"📌 Reason: {reason}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close"))
    fig.add_trace(go.Scatter(x=df.index, y=ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator(), name="SMA(20)"))
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ Failed to analyze selected asset: {e}")

# --- Bulk Scan for Best BUY/SELL ---
st.markdown("---")
st.subheader("📈 Scanning All Assets for Signals...")

def scan_asset(name, sym):
    try:
        data = get_data(sym)
        sig, _, _, _, _, _, price = calculate_signal(data, logic_mode)
        return name, sig, price
    except:
        return None

with concurrent.futures.ThreadPoolExecutor() as executor:
    results = list(executor.map(lambda item: scan_asset(*item), assets.items()))

best_buys = [(name, price) for name, sig, price in results if sig == "BUY"] if results else []
best_sells = [(name, price) for name, sig, price in results if sig == "SELL"] if results else []

# --- Detect and show alerts for new BUY/SELL signals ---
def detect_alerts(new_assets, prev_assets, label):
    new_set = set(a[0] for a in new_assets)
    old_set = set(prev_assets)
    new_items = new_set - old_set
    if new_items:
        for item in new_items:
            st.success(f"🔔 New {label} Signal: **{item}**")
    return list(new_set)

st.markdown("---")
st.subheader("🚀 Best Assets to Buy Now")
if best_buys:
    st.session_state.prev_buy_assets = detect_alerts(best_buys, st.session_state.prev_buy_assets, "BUY")
    for name, price in best_buys:
        st.markdown(f"🟢 **{name}** — ${price:.2f}")
else:
    st.write("No BUY signals found right now.")

st.markdown("---")
st.subheader("⚠️ Best Assets to Sell Now")
if best_sells:
    st.session_state.prev_sell_assets = detect_alerts(best_sells, st.session_state.prev_sell_assets, "SELL")
    for name, price in best_sells:
        st.markdown(f"🔴 **{name}** — ${price:.2f}")
else:
    st.write("No SELL signals found right now.")
