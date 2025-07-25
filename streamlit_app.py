import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import concurrent.futures

st.set_page_config(page_title="📈 Signal Scout Global", layout="centered")
st.title("📈 Signal Scout Global")
st.write("Analyze global S&P 500 stocks (500+), crypto, commodities, forex with Buy/Sell/Hold signals.")

@st.cache_data(ttl=86400)
def load_sp500_symbols():
    url = "https://datahub.io/core/s-and-p-500-companies/r/constituents.csv"
    df = pd.read_csv(url)
    # Confirm columns exist
    required_cols = {'Symbol', 'Name'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV missing columns {required_cols - set(df.columns)}")
    # Append .US suffix for yfinance tickers
    return dict(zip(df['Symbol'] + " (" + df['Name'] + ")", df['Symbol'] + ".US"))

sp500_assets = load_sp500_symbols()

other_assets = {
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Gold (GC=F)": "GC=F",
    "Silver (SI=F)": "SI=F",
    "Crude Oil WTI (CL=F)": "CL=F",
    "Brent Oil (BZ=F)": "BZ=F",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
}

assets = {**sp500_assets, **other_assets}

selected_asset = st.selectbox("Choose an asset:", list(assets.keys()))
ticker = assets[selected_asset]
logic_mode = st.selectbox("Logic Mode:", ["Simple", "Combined"])

@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    df.dropna(inplace=True)
    return df

def calculate_signal(df, logic_mode):
    close = df['Close'].squeeze()
    rsi = ta.momentum.RSIIndicator(close).rsi()
    sma = ta.trend.SMAIndicator(close,20).sma_indicator()
    macd = ta.trend.MACD(close)
    macd_line = macd.macd()
    macd_signal = macd.macd_signal()

    vals = {k: float(v.iloc[-1]) for k, v in {
        'rsi': rsi, 'sma': sma, 'macd': macd_line, 'macd_signal': macd_signal
    }.items()}
    close_val = float(close.iloc[-1])
    signal = "HOLD"; reason = ""

    if logic_mode == "Simple":
        if vals['rsi'] < 30:
            signal, reason = "BUY", "RSI < 30 (Oversold)"
        elif vals['rsi'] > 70:
            signal, reason = "SELL", "RSI > 70 (Overbought)"
    else:
        if vals['rsi'] < 30 and close_val > vals['sma'] and vals['macd'] > vals['macd_signal']:
            signal, reason = "BUY", "RSI < 30 + Price > SMA + MACD crossover"
        elif vals['rsi'] > 70 and close_val < vals['sma'] and vals['macd'] < vals['macd_signal']:
            signal, reason = "SELL", "RSI > 70 + Price < SMA + MACD cross down"

    return signal, reason, vals['rsi'], vals['sma'], vals['macd'], vals['macd_signal'], close_val

# Persistent previous buy/sell signals for notifications
if 'prev_buy' not in st.session_state:
    st.session_state.prev_buy = []
if 'prev_sell' not in st.session_state:
    st.session_state.prev_sell = []

# Selected asset detail view
try:
    df = get_data(ticker)
    sig, reason, rsi_val, sma_val, macd_val, macd_sig_val, close_val = calculate_signal(df, logic_mode)

    st.markdown("---")
    st.subheader(f"📊 {selected_asset}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Price", f"${close_val:.2f}")
    col2.metric("RSI", f"{rsi_val:.2f}")
    col3.metric("SMA(20)", f"{sma_val:.2f}")
    st.write(f"MACD: {macd_val:.2f} | Signal: {macd_sig_val:.2f}")
    color = {"BUY":"🟢","SELL":"🔴","HOLD":"🟡"}[sig]
    st.markdown(f"### Signal: {color} {sig}")
    if reason: st.caption(reason)

    dfc = df[['Close']].copy()
    dfc["SMA 20"] = ta.trend.SMAIndicator(df['Close'], 20).sma_indicator()
    dfc = dfc.dropna()
    st.line_chart(dfc)

except Exception as e:
    st.error(f"Failed to analyze selected asset: {e}")

# Bulk scan all assets concurrently
def scan(name, sym):
    try:
        data = get_data(sym)
        signal, _, _, _, _, _, price = calculate_signal(data, logic_mode)
        return (name, signal, price)
    except Exception:
        return None

st.markdown("---")
st.subheader("📈 Scanning All Assets")

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    raw_results = list(executor.map(lambda item: scan(*item), assets.items()))

results = [r for r in raw_results if r]

buys = [(n, p) for n, s, p in results if s == "BUY"]
sells = [(n, p) for n, s, p in results if s == "SELL"]

def detect(new_list, prev_list, label):
    new_names = set(n for n, _ in new_list)
    old_names = set(prev_list)
    added = new_names - old_names
    if added:
        for asset_name in added:
            st.success(f"🔔 New {label}: {asset_name}")
    return list(new_names)

st.write("🚀 Buys:")
if buys:
    st.session_state.prev_buy = detect(buys, st.session_state.prev_buy, "BUY")
    for n, p in buys:
        st.write(f"🟢 {n} — ${p:.2f}")
else:
    st.write("No BUY signals.")

st.write("⚠️ Sells:")
if sells:
    st.session_state.prev_sell = detect(sells, st.session_state.prev_sell, "SELL")
    for n, p in sells:
        st.write(f"🔴 {n} — ${p:.2f}")
else:
    st.write("No SELL signals.")
