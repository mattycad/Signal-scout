import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.title("Enhanced Market Signal App with Search & Portfolio View")

# Full asset dictionary
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

# Flatten asset list for search
all_assets = []
for cat, lst in assets.items():
    all_assets.extend(lst)

# Search box for asset selection
search_term = st.text_input("Search assets (type ticker or partial):").upper()

filtered_assets = [a for a in all_assets if search_term in a] if search_term else all_assets

selected_assets = st.multiselect("Select one or more assets", filtered_assets, default=filtered_assets[:3])

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

if not selected_assets:
    st.warning("Please select at least one asset.")
    st.stop()

# Download data for all selected assets
all_data = {}
for asset in selected_assets:
    df = yf.download(asset, period="60d", interval="1d")
    if df.empty:
        st.error(f"No data found for {asset}")
        continue
    all_data[asset] = df

# Show combined normalized price chart
if all_data:
    st.header("Normalized Close Prices (for comparison)")
    norm_close = pd.DataFrame()
    for asset, df in all_data.items():
        norm_close[asset] = df["Close"] / df["Close"].iloc[0]
    st.line_chart(norm_close)

# Show individual asset details & indicators
for asset, df in all_data.items():
    st.subheader(f"Analysis for {asset}")
    df["MA7"] = df["Close"].rolling(window=7).mean()
    df["MA21"] = df["Close"].rolling(window=21).mean()
    df["RSI14"] = compute_rsi(df["Close"])
    df["MACD"], df["MACD_Signal"] = compute_macd(df["Close"])

    latest = df.iloc[-1]

    st.write(f"Latest Close: {latest['Close']:.2f}")
    st.write(f"7-day MA: {latest['MA7']:.2f}")
    st.write(f"21-day MA: {latest['MA21']:.2f}")
    st.write(f"RSI(14): {latest['RSI14']:.2f}")
    st.write(f"MACD: {latest['MACD']:.4f}")
    st.write(f"MACD Signal: {latest['MACD_Signal']:.4f}")

    # Simple buy/sell logic example:
    buy_signal = (latest['MA7'] > latest['MA21']) and (latest['RSI14'] < 70) and (latest['MACD'] > latest['MACD_Signal'])
    sell_signal = (latest['MA7'] < latest['MA21']) and (latest['RSI14'] > 30) and (latest['MACD'] < latest['MACD_Signal'])

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
