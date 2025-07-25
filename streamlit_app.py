import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.title("Market Signal App with Asset Dropdown")

# Assets dictionary with categories
assets = {
    "Stocks": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "ADBE", "CRM", "INTC",
        "JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "BLK", "PNC", "USB",
        "JNJ", "PFE", "MRK", "ABBV", "TMO", "ABT", "BMY", "LLY", "DHR", "MDT",
        "KO", "PEP", "PG", "PM", "MO", "MCD", "SBUX", "TGT", "WMT", "COST",
        "XOM", "CVX", "COP", "EOG", "SLB", "PSX", "VLO", "MPC", "KMI", "OXY",
        "BA", "CAT", "DE", "LMT", "GE", "MMM", "UTX", "HON", "FDX", "UPS",
        "T", "VZ", "DIS", "NFLX", "CHTR", "CMCSA", "SIRI", "TMUS", "DISH", "FOXA",
        "NEE", "DUK", "SO", "AEP", "EXC", "D", "EIX", "PEG", "ED", "PPL",
        "PLD", "SPG", "PSA", "O", "EQIX", "WELL", "AVB", "VTR", "EQR", "ESS",
        "BABA", "TCEHY", "TM", "SONY", "NSRGY", "RDS-A", "BMY", "SNY", "BP", "SAP", "HSBA.L",
        "SPY", "QQQ", "DIA", "IWM", "VTI", "EFA", "VWO", "GLD", "USO", "TLT"
    ],
    "Commodities": [
        "GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "PL=F", "PA=F", "ZC=F", "ZS=F", "ZW=F"
    ],
    "Currencies": [
        "EURUSD=X", "JPY=X", "GBPUSD=X", "AUDUSD=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X", "EURJPY=X", "EURGBP=X", "USDNOK=X"
    ],
    "Cryptocurrency": [
        "BTC-USD", "ETH-USD", "BNB-USD", "ADA-USD", "SOL-USD", "XRP-USD", "DOT-USD", "LTC-USD", "AVAX-USD", "DOGE-USD"
    ]
}

# Create a flat list of assets with category labels for the dropdown
dropdown_options = []
for category, symbols in assets.items():
    dropdown_options.append(f"--- {category} ---")  # category header
    dropdown_options.extend(symbols)

# Remove duplicates or empty strings if any
dropdown_options = [opt for opt in dropdown_options if opt.strip() != ""]

# Streamlit selectbox does not support grouping natively,
# so category headers are shown as disabled options visually by prefix "---"

selected_asset = st.selectbox("Select an asset", dropdown_options)

# If user selects a category header (starts with ---), prompt them to select a real asset
if selected_asset.startswith("---"):
    st.info("Please select an actual asset, not a category header.")
    st.stop()

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def safe_fmt(value, digits=2):
    return f"{value:.{digits}f}" if pd.notna(value) else "N/A"

# Download data for selected asset
df = yf.download(selected_asset, period="60d", interval="1d")

if df.empty:
    st.error(f"No data found for {selected_asset}")
    st.stop()

st.header(f"Analysis for {selected_asset}")

df["MA7"] = df["Close"].rolling(window=7).mean()
df["MA21"] = df["Close"].rolling(window=21).mean()
df["RSI14"] = compute_rsi(df["Close"])
df["MACD"], df["MACD_Signal"] = compute_macd(df["Close"])

latest = df.iloc[-1]

st.write(f"Latest Close: {safe_fmt(latest['Close'])}")
st.write(f"7-day MA: {safe_fmt(latest['MA7'])}")
st.write(f"21-day MA: {safe_fmt(latest['MA21'])}")
st.write(f"RSI(14): {safe_fmt(latest['RSI14'])}")
st.write(f"MACD: {safe_fmt(latest['MACD'], 4)}")
st.write(f"MACD Signal: {safe_fmt(latest['MACD_Signal'], 4)}")

# Simple buy/sell logic example:
buy_signal = (
    pd.notna(latest['MA7']) and pd.notna(latest['MA21']) and pd.notna(latest['RSI14']) and pd.notna(latest['MACD']) and pd.notna(latest['MACD_Signal'])
    and (latest['MA7'] > latest['MA21']) and (latest['RSI14'] < 70) and (latest['MACD'] > latest['MACD_Signal'])
)
sell_signal = (
    pd.notna(latest['MA7']) and pd.notna(latest['MA21']) and pd.notna(latest['RSI14']) and pd.notna(latest['MACD']) and pd.notna(latest['MACD_Signal'])
    and (latest['MA7'] < latest['MA21']) and (latest['RSI14'] > 30) and (latest['MACD'] < latest['MACD_Signal'])
)

if buy_signal:
    st.success("Signal: BUY")
elif sell_signal:
    st.error("Signal: SELL")
else:
    st.info("Signal: HOLD")

st.line_chart(df[["Close", "MA7", "MA21"]])
st.line_chart(df[["RSI14"]])
macd_df = df[["MACD", "MACD_Signal"]].dropna()
st.line_chart(macd_df)

st.write("**Note:** This app provides simple technical indicator signals and is for educational purposes only.")
