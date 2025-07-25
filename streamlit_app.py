import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# RSI calculation helper
def RSI(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Signal generator, now accepts dynamic price column name
def generate_signals(data, price_col='Close'):
    data = data.copy()
    data['MA20'] = data[price_col].rolling(window=20).mean()
    data['MA50'] = data[price_col].rolling(window=50).mean()
    data['RSI'] = RSI(data[price_col], 14)

    signal = "Hold"

    if len(data) < 2:
        return signal, np.nan, np.nan, np.nan, np.nan

    prev_ma20 = data['MA20'].iloc[-2]
    prev_ma50 = data['MA50'].iloc[-2]
    last_ma20 = data['MA20'].iloc[-1]
    last_ma50 = data['MA50'].iloc[-1]
    last_rsi = data['RSI'].iloc[-1]
    last_close = data[price_col].iloc[-1]

    if not any(pd.isna([prev_ma20, prev_ma50, last_ma20, last_ma50])):
        if prev_ma20 < prev_ma50 and last_ma20 > last_ma50:
            signal = "Buy"
        elif prev_ma20 > prev_ma50 and last_ma20 < last_ma50:
            signal = "Sell"

    if not pd.isna(last_rsi):
        if last_rsi < 30:
            signal = "Buy"
        elif last_rsi > 70:
            signal = "Sell"

    return signal, last_close, last_ma20, last_ma50, last_rsi


st.title("Multi-Market Real-Time Signal Scout")

market_type = st.selectbox("Select Market Type", ["Stocks", "Cryptocurrency", "Currencies", "Commodities"])

# Define your symbol lists for each market type here
stocks = ["AAPL", "MSFT", "TSLA", "GOOGL"]
cryptos = ["BTC-USD", "ETH-USD", "DOGE-USD"]
currencies = ["EURUSD=X", "JPY=X", "GBPUSD=X"]
commodities = ["GC=F", "CL=F", "SI=F"]

if market_type == "Stocks":
    symbol = st.selectbox("Select Stock", stocks)
elif market_type == "Cryptocurrency":
    symbol = st.selectbox("Select Crypto", cryptos)
elif market_type == "Currencies":
    symbol = st.selectbox("Select Currency Pair", currencies)
else:
    symbol = st.selectbox("Select Commodity", commodities)

data_load_state = st.text("Loading data...")
data = yf.download(symbol, period="2mo", interval="1d", progress=False)

if data is None or data.empty:
    st.error("Failed to load data for symbol: " + symbol)
else:
    # Determine the price column: prefer 'Close', fallback 'Adj Close'
    if 'Close' in data.columns:
        price_col = 'Close'
    elif 'Adj Close' in data.columns:
        price_col = 'Adj Close'
    else:
        st.error("No 'Close' or 'Adj Close' column found in data.")
        price_col = None

    if price_col:
        signal, price, ma20, ma50, rsi = generate_signals(data, price_col=price_col)
        data_load_state.text("Data loaded.")

        try:
            price = float(price)
        except Exception:
            price = np.nan

        if pd.isna(price):
            st.subheader(f"Latest price for {symbol}: Data unavailable")
        else:
            st.subheader(f"Latest price for {symbol}: ${price:.4f}")

        st.write(f"Signal: **{signal}**")

        if not pd.isna(ma20) and not pd.isna(ma50) and not pd.isna(rsi):
            st.write(f"MA20: {ma20:.4f} | MA50: {ma50:.4f} | RSI: {rsi:.2f}")

        # Prepare columns for plotting safely
        plot_cols = [price_col, 'MA20', 'MA50']
        if all(col in data.columns or col in ['MA20', 'MA50'] for col in plot_cols):
            # Ensure MAs are in data for plotting
            data_plot = data[[price_col]].copy()
            data_plot['MA20'] = data[price_col].rolling(window=20).mean()
            data_plot['MA50'] = data[price_col].rolling(window=50).mean()
            st.line_chart(data_plot.dropna())
        else:
            st.warning("Insufficient data columns for chart plotting.")
