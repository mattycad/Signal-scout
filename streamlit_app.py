import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.set_page_config(page_title="📈 Signal Scout Global", layout="wide")
st.title("📈 Signal Scout Global")
st.write("Real-time signals for global stocks, crypto, commodities & currencies.")

# === ASSET CATEGORIES ===
assets = {
    "STOCKS": {
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Amazon (AMZN)": "AMZN",
        "Google (GOOGL)": "GOOGL",
        "Microsoft (MSFT)": "MSFT",
        "NVIDIA (NVDA)": "NVDA",
        "HSBC (HSBA.L)": "HSBA.L",
        "Shell (SHEL.L)": "SHEL.L",
        "Rolls-Royce (RR.L)": "RR.L"
    },
    "CRYPTO": {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Solana (SOL)": "SOL-USD",
        "Cardano (ADA)": "ADA-USD",
        "XRP": "XRP-USD",
        "Dogecoin (DOGE)": "DOGE-USD",
        "Litecoin (LTC)": "LTC-USD"
    },
    "COMMODITIES": {
        "Gold": "GC=F",
        "Silver": "SI=F",
        "Crude Oil": "CL=F",
        "Natural Gas": "NG=F"
    },
    "CURRENCIES": {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "USD/JPY": "JPY=X",
        "USD/CHF": "CHF=X",
        "USD/CAD": "CAD=X"
    }
}

logic_mode = st.selectbox("Select Signal Logic Mode", ["Simple", "Combined"])

@st.cache_data(ttl=600)
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    df.dropna(inplace=True)
    return df

def calculate_signal(df, logic="Simple"):
    close = df["Close"]

    rsi = ta.momentum.RSIIndicator(close).rsi().squeeze()
    sma_20 = ta.trend.SMAIndicator(close, window=20).sma_indicator().squeeze()
    macd_obj = ta.trend.MACD(close)
    macd = macd_obj.macd().squeeze()
    macd_sig = macd_obj.macd_signal().squeeze()

    latest_close = close.iloc[-1]
    latest_rsi = rsi.iloc[-1]
    latest_sma = sma_20.iloc[-1]
    latest_macd = macd.iloc[-1]
    latest_macd_sig = macd_sig.iloc[-1]

    signal = "HOLD"
    reason = ""

    if logic == "Simple":
        if latest_rsi < 30:
            signal = "BUY"
            reason = "RSI < 30 (Oversold)"
        elif latest_rsi > 70:
            signal = "SELL"
            reason = "RSI > 70 (Overbought)"
    else:
        if latest_rsi < 30 and latest_close > latest_sma and latest_macd > latest_macd_sig:
            signal = "BUY"
            reason = "RSI < 30 + Price > SMA + MACD crossover"
        elif latest_rsi > 70 and latest_close < latest_sma and latest_macd < latest_macd_sig:
            signal = "SELL"
            reason = "RSI > 70 + Price < SMA + MACD cross down"

    return signal, reason, latest_rsi, latest_sma, latest_macd, latest_macd_sig, latest_close

# === Session state to track alerts ===
if "prev_buys" not in st.session_state:
    st.session_state.prev_buys = set()
if "prev_sells" not in st.session_state:
    st.session_state.prev_sells = set()

buy_assets = set()
sell_assets = set()
buy_prices = {}
sell_prices = {}

st.header("📊 Market Signal Overview")

with st.spinner("Analyzing markets..."):
    for category, items in assets.items():
        st.subheader(f"🔍 {category}")
        for name, symbol in items.items():
            try:
                df = get_data(symbol)
                signal, reason, rsi, sma, macd, macd_sig, price = calculate_signal(df, logic_mode)

                if signal == "BUY":
                    buy_assets.add(name)
                    buy_prices[name] = price
                elif signal == "SELL":
                    sell_assets.add(name)
                    sell_prices[name] = price

                st.markdown(f"**{name}** — Signal: `{signal}` | Price: ${price:.2f} | RSI: {rsi:.2f}")

            except Exception as e:
                st.warning(f"⚠️ Could not analyze {name}: {e}")

# === ALERTS ===
new_buys = buy_assets - st.session_state.prev_buys
new_sells = sell_assets - st.session_state.prev_sells

if new_buys:
    for name in new_buys:
        st.success(f"🛎️ NEW BUY SIGNAL: **{name}** at ${buy_prices[name]:.2f}")
if new_sells:
    for name in new_sells:
        st.warning(f"🔔 NEW SELL SIGNAL: **{name}** at ${sell_prices[name]:.2f}")

# === DISPLAY ACTIVE SIGNALS ===
st.markdown("---")
st.subheader("🟢 Current Best BUY Signals")
if buy_assets:
    for name in sorted(buy_assets):
        st.write(f"✅ **{name}** — ${buy_prices[name]:.2f}")
else:
    st.write("No strong BUY signals.")

st.subheader("🔴 Current Best SELL Signals")
if sell_assets:
    for name in sorted(sell_assets):
        st.write(f"🚨 **{name}** — ${sell_prices[name]:.2f}")
else:
    st.write("No strong SELL signals.")

# === Update session state for alert tracking ===
st.session_state.prev_buys = buy_assets
st.session_state.prev_sells = sell_assets
