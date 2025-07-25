import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import concurrent.futures
import datetime

st.set_page_config(page_title="📈 Signal Scout: Multi-Asset Alerts", layout="wide")
st.title("📈 Signal Scout: Stocks, Crypto, Commodities & Forex")

st.write("Analyze multiple asset classes with Buy/Sell/Hold signals and alerts on changes.")

# Expanded Assets list (Stocks, Crypto, Commodities, Forex)
ASSETS = {
    # Stocks (popular & diverse sectors)
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Tesla (TSLA)": "TSLA",
    "Amazon (AMZN)": "AMZN",
    "Alphabet (GOOGL)": "GOOGL",
    "Meta (META)": "META",
    "NVIDIA (NVDA)": "NVDA",
    "JPMorgan Chase (JPM)": "JPM",
    "Johnson & Johnson (JNJ)": "JNJ",
    "Visa (V)": "V",
    "Walmart (WMT)": "WMT",
    "Coca-Cola (KO)": "KO",
    
    # Crypto
    "Bitcoin (BTC-USD)": "BTC-USD",
    "Ethereum (ETH-USD)": "ETH-USD",
    "Binance Coin (BNB-USD)": "BNB-USD",
    "Cardano (ADA-USD)": "ADA-USD",
    "Solana (SOL-USD)": "SOL-USD",
    
    # Commodities
    "Gold (GC=F)": "GC=F",
    "Silver (SI=F)": "SI=F",
    "Crude Oil WTI (CL=F)": "CL=F",
    "Brent Oil (BZ=F)": "BZ=F",
    "Natural Gas (NG=F)": "NG=F",
    "Copper (HG=F)": "HG=F",
    
    # Forex major pairs
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "USD/CHF": "CHF=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "NZD/USD": "NZDUSD=X",
}

@st.cache_data(ttl=300)
def fetch_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df.empty or 'Close' not in df.columns:
        raise ValueError(f"No data for {ticker}")
    df.dropna(inplace=True)
    return df

def compute_signal(df):
    close = df['Close']
    if len(close) < 21:
        return "HOLD", "Insufficient data", None

    # Indicators
    rsi = ta.momentum.RSIIndicator(close).rsi()
    sma20 = ta.trend.SMAIndicator(close, 20).sma_indicator()
    macd = ta.trend.MACD(close)
    macd_line = macd.macd()
    macd_signal = macd.macd_signal()

    # Use last valid values
    rsi_val = rsi.dropna().iloc[-1]
    sma_val = sma20.dropna().iloc[-1]
    macd_val = macd_line.dropna().iloc[-1]
    macd_sig_val = macd_signal.dropna().iloc[-1]
    price = close.iloc[-1]

    # Simple logic:
    if rsi_val < 30 and price > sma_val and macd_val > macd_sig_val:
        return "BUY", "RSI < 30, Price > SMA20, MACD bullish crossover", price
    elif rsi_val > 70 and price < sma_val and macd_val < macd_sig_val:
        return "SELL", "RSI > 70, Price < SMA20, MACD bearish crossover", price
    else:
        return "HOLD", "No clear signal", price

if 'signals' not in st.session_state:
    st.session_state.signals = {}

def scan_assets():
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_data, ticker): name for name, ticker in ASSETS.items()}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                df = future.result()
                signal, reason, price = compute_signal(df)
                results[name] = {"signal": signal, "reason": reason, "price": price}
            except Exception as e:
                results[name] = {"signal": "HOLD", "reason": "Error loading data", "price": None}
    return results

st.header("🚀 Asset Signals")

with st.spinner("Fetching data and analyzing..."):
    current_signals = scan_assets()

buy_list, sell_list, hold_list = [], [], []

for asset, info in current_signals.items():
    sig = info['signal']
    reason = info['reason']
    price = info['price']

    prev_sig = st.session_state.signals.get(asset)
    if prev_sig != sig and prev_sig is not None:
        st.info(f"🔔 Signal change for **{asset}**: {prev_sig} → {sig}")

    st.session_state.signals[asset] = sig

    if sig == "BUY":
        buy_list.append((asset, price, reason))
    elif sig == "SELL":
        sell_list.append((asset, price, reason))
    else:
        hold_list.append((asset, price, reason))

def show_assets(title, assets):
    st.subheader(title)
    if not assets:
        st.write("None")
    else:
        for name, price, reason in sorted(assets, key=lambda x: x[1] or 0, reverse=True):
            price_str = f"${price:.2f}" if price else "N/A"
            st.write(f"- **{name}**: {price_str} — {reason}")

show_assets("🟢 Buy Signals", buy_list)
show_assets("🔴 Sell Signals", sell_list)
show_assets("🟡 Hold Signals", hold_list)

st.markdown("---")
st.caption(f"Last update: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
