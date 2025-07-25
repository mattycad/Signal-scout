import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import concurrent.futures
import datetime

st.set_page_config(page_title="📈 Signal Scout Global", layout="centered")
st.title("📈 Signal Scout Global")
st.write("Analyze global S&P 500 stocks (500+), crypto, commodities, forex with Buy/Sell/Hold signals.")

@st.cache_data(ttl=86400)
def load_sp500_symbols():
    try:
        url = "https://raw.githubusercontent.com/rahulbordoloi/snp500/main/snp500.csv"
        df = pd.read_csv(url)
        if not {"Symbol", "Security"}.issubset(df.columns):
            raise ValueError("CSV missing expected columns.")
        return dict(zip(df['Symbol'] + " (" + df['Security'] + ")", df['Symbol'] + ".US"))
    except Exception as e:
        st.warning("⚠️ Could not load S&P 500 symbols. Falling back to default.")
        return {
            "Apple (AAPL)": "AAPL.US",
            "Microsoft (MSFT)": "MSFT.US",
            "Amazon (AMZN)": "AMZN.US"
        }

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

@st.cache_data(ttl=300)
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df.empty or "Close" not in df.columns:
        raise ValueError(f"No valid price data for {ticker}")
    df.dropna(inplace=True)
    return df

def calculate_signal(df, logic_mode):
    close = df['Close'].dropna()
    if len(close) < 21:
        raise ValueError("Not enough data to calculate indicators.")

    rsi = ta.momentum.RSIIndicator(close).rsi()
    sma = ta.trend.SMAIndicator(close, 20).sma_indicator()
    macd = ta.trend.MACD(close)
    macd_line = macd.macd()
    macd_signal = macd.macd_signal()

    if any(len(s.dropna()) < 1 for s in [rsi, sma, macd_line, macd_signal]):
        raise ValueError("Not enough indicator data.")

    vals = {k: float(v.dropna().iloc[-1]) for k, v in {
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

if 'prev_buy' not in st.session_state:
    st.session_state.prev_buy = []
if 'prev_sell' not in st.session_state:
    st.session_state.prev_sell = []

try:
    with st.spinner("📡 Downloading asset data..."):
        df = get_data(ticker)
        sig, reason, rsi_val, sma_val, macd_val, macd_sig_val, close_val = calculate_signal(df, logic_mode)

    st.markdown("---")
    st.subheader(f"📊 {selected_asset}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Price", f"${close_val:.2f}")
    col2.metric("RSI", f"{rsi_val:.2f}")
    col3.metric("SMA(20)", f"{sma_val:.2f}")
    st.write(f"MACD: {macd_val:.2f} | Signal: {macd_sig_val:.2f}")
    color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}[sig]
    st.markdown(f"### Signal: {color} {sig}")
    if reason: st.caption(reason)

    dfc = df[['Close']].copy()
    dfc["SMA 20"] = ta.trend.SMAIndicator(df['Close'], 20).sma_indicator()
    dfc.dropna(inplace=True)

    with st.expander("📈 Show Price Chart"):
        st.line_chart(dfc)

except Exception as e:
    st.error(f"Failed to analyze selected asset: {e}")

def scan(name, sym):
    try:
        d = get_data(sym)
        s, _, _, _, _, _, p = calculate_signal(d, logic_mode)
        return (name, s, p)
    except:
        return None

st.markdown("---")
st.subheader("📈 Scanning All Assets")

with st.spinner("🔍 Scanning for Buy/Sell signals..."):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        raw = list(ex.map(lambda item: scan(*item), assets.items()))
    results = [r for r in raw if r]

    buys = [(n, p) for n, s, p in results if s == "BUY"]
    sells = [(n, p) for n, s, p in results if s == "SELL"]

def detect_changes(new, old, label):
    new_names = set(n for n, _ in new)
    old_names = set(old)
    added = new_names - old_names
    removed = old_names - new_names

    for a in added:
        st.success(f"🔔 New {label}: {a}")
    for r in removed:
        st.warning(f"💡 Consider Closing: {r} is no longer a {label}")

    return list(new_names)

st.write("🚀 Buys:")
if buys:
    st.session_state.prev_buy = detect_changes(buys, st.session_state.prev_buy, "BUY")
    for n, p in buys:
        st.write(f"🟢 {n} — ${p:.2f}")
else:
    st.write("No BUY signals.")

st.write("⚠️ Sells:")
if sells:
    st.session_state.prev_sell = detect_changes(sells, st.session_state.prev_sell, "SELL")
    for n, p in sells:
        st.write(f"🔴 {n} — ${p:.2f}")
else:
    st.write("No SELL signals.")

st.markdown("---")
st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
