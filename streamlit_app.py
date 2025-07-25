import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests

st.set_page_config(page_title="Multi-Market Signal Scout", layout="wide")

# --- Utility Functions ---

def fetch_yahoo_data(ticker, period='1mo', interval='5m'):
    """Fetch historical data from Yahoo Finance."""
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if data.empty:
            st.error(f"No data for ticker {ticker}")
        return data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return None

def fetch_crypto_price(symbol):
    """Fetch current price for a crypto from CoinGecko API."""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    try:
        r = requests.get(url)
        r.raise_for_status()
        price = r.json()[symbol]['usd']
        return price
    except Exception as e:
        st.error(f"Error fetching crypto price for {symbol}: {e}")
        return None

# --- Technical Indicators ---

def moving_average(data, window):
    return data['Close'].rolling(window=window).mean()

def RSI(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    RS = gain / loss
    return 100 - (100 / (1 + RS))

# --- Signal Generation ---

def generate_signals(data):
    data = data.copy()
    data['MA20'] = moving_average(data, 20)
    data['MA50'] = moving_average(data, 50)
    data['RSI'] = RSI(data['Close'], 14)

    signal = "Hold"

    # Need at least 2 rows to compare previous and last values
    if len(data) < 2:
        return signal, np.nan, np.nan, np.nan, np.nan

    prev_ma20 = data['MA20'].iloc[-2]
    prev_ma50 = data['MA50'].iloc[-2]
    last_ma20 = data['MA20'].iloc[-1]
    last_ma50 = data['MA50'].iloc[-1]
    last_rsi = data['RSI'].iloc[-1]
    last_close = data['Close'].iloc[-1]

    # Skip signal logic if any relevant value is NaN
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

# --- Asset Lists ---

stock_symbols = ['AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN']
commodity_symbols = ['GC=F', 'CL=F', 'SI=F']  # Gold, Crude Oil, Silver futures Yahoo tickers
currency_pairs = ['EURUSD=X', 'JPY=X', 'GBPUSD=X']  # Yahoo FX pairs
crypto_map = {  # CoinGecko IDs to symbols
    'bitcoin': 'BTC',
    'ethereum': 'ETH',
    'ripple': 'XRP',
    'cardano': 'ADA'
}

# --- Streamlit UI ---

st.title("Multi-Market Real-Time Signal Scout")

market = st.selectbox("Select Market Type", ['Stocks', 'Commodities', 'Currencies', 'Cryptocurrency'])

if market != 'Cryptocurrency':
    if market == 'Stocks':
        symbol = st.selectbox("Select Stock", stock_symbols)
    elif market == 'Commodities':
        symbol = st.selectbox("Select Commodity", commodity_symbols)
    else:
        symbol = st.selectbox("Select Currency Pair", currency_pairs)

    data_load_state = st.text("Loading data...")
    data = fetch_yahoo_data(symbol)
    if data is not None and not data.empty:
        signal, price, ma20, ma50, rsi = generate_signals(data)
        data_load_state.text("Data loaded.")

        # Defensive conversion to scalar float for price
        try:
            price = float(price)
        except Exception:
            price = np.nan

        if pd.isna(price):
            st.subheader(f"Latest price for {symbol}: Data unavailable")
        else:
            st.subheader(f"Latest price for {symbol}: ${price:.2f}")

        st.write(f"Signal: **{signal}**")
        if not pd.isna(ma20) and not pd.isna(ma50) and not pd.isna(rsi):
            st.write(f"MA20: {ma20:.2f} | MA50: {ma50:.2f} | RSI: {rsi:.2f}")

        st.line_chart(data[['Close', 'MA20', 'MA50']].dropna())
    else:
        data_load_state.text("Failed to load data.")

else:
    # Crypto
    crypto = st.selectbox("Select Cryptocurrency", list(crypto_map.values()))
    coingecko_id = None
    for k, v in crypto_map.items():
        if v == crypto:
            coingecko_id = k
            break

    price = fetch_crypto_price(coingecko_id)
    if price is not None:
        st.subheader(f"Latest price for {crypto}: ${price:.4f}")
        st.write("Signals for crypto are based on price momentum (demo).")

        @st.cache_data(ttl=600)
        def fetch_crypto_historical(coin_id, days=30):
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval=daily"
            r = requests.get(url)
            r.raise_for_status()
            prices = r.json()['prices']
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df

        hist = fetch_crypto_historical(coingecko_id)
        hist['MA10'] = hist['price'].rolling(window=10).mean()
        hist['MA20'] = hist['price'].rolling(window=20).mean()

        if len(hist) >= 2 and not hist[['MA10', 'MA20']].isna().any().any():
            last = hist.iloc[-1]
            prev = hist.iloc[-2]
            signal = "Hold"
            if prev['MA10'] < prev['MA20'] and last['MA10'] > last['MA20']:
                signal = "Buy"
            elif prev['MA10'] > prev['MA20'] and last['MA10'] < last['MA20']:
                signal = "Sell"
            st.write(f"Signal based on MA crossover: **{signal}**")
        else:
            st.write("Insufficient data to generate signal.")

        st.line_chart(hist[['price', 'MA10', 'MA20']])

st.markdown("---")
st.write("Data sources: Yahoo Finance (stocks, commodities, FX), CoinGecko (crypto).")
