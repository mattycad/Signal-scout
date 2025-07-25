import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Multi-Market Real-Time Signal Scout", layout="wide")

# --- Signal generation function ---
def generate_signals(df):
    data = df.copy()
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA50'] = data['Close'].rolling(window=50).mean()
    
    delta = data['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    # Ensure gain and loss are 1D Series with correct index
    gain = pd.Series(gain, index=data.index)
    loss = pd.Series(loss, index=data.index)

    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()

    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))

    signal = "Hold"
    if len(data) >= 2:
        last = data.iloc[-1]
        prev = data.iloc[-2]
        if (
            not pd.isna(prev['MA20']) and not pd.isna(prev['MA50']) and
            not pd.isna(last['MA20']) and not pd.isna(last['MA50'])
        ):
            if prev['MA20'] < prev['MA50'] and last['MA20'] > last['MA50']:
                signal = "Buy"
            elif prev['MA20'] > prev['MA50'] and last['MA20'] < last['MA50']:
                signal = "Sell"

    price = data['Close'].iloc[-1] if 'Close' in data.columns else np.nan
    ma20 = data['MA20'].iloc[-1] if 'MA20' in data.columns else np.nan
    ma50 = data['MA50'].iloc[-1] if 'MA50' in data.columns else np.nan
    rsi = data['RSI'].iloc[-1] if 'RSI' in data.columns else np.nan

    return signal, price, ma20, ma50, rsi, data

# --- Sidebar Market Selector ---
st.title("📊 Multi-Market Real-Time Signal Scout")
market_type = st.sidebar.selectbox("Select Market Type", ["Stocks", "Crypto", "Commodities", "Currencies"])

# --- Symbol Pickers ---
symbol = ""
if market_type == "Stocks":
    symbol = st.sidebar.selectbox("Select Stock", ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"])
elif market_type == "Crypto":
    symbol = st.sidebar.selectbox("Select Cryptocurrency", ["BTC-USD", "ETH-USD", "XRP-USD"])
elif market_type == "Commodities":
    symbol = st.sidebar.selectbox("Select Commodity", ["GC=F", "CL=F", "SI=F", "NG=F"])  # Gold, Oil, Silver, Gas
elif market_type == "Currencies":
    symbol = st.sidebar.selectbox("Select Currency Pair", ["EURUSD=X", "GBPUSD=X", "JPY=X", "USDCAD=X"])

# --- Data Fetching and Display ---
if symbol:
    st.write("Loading data...")
    try:
        end = datetime.today()
        start = end - timedelta(days=180)
        data = yf.download(symbol, start=start, end=end, interval='1d')
        
        if data.empty or 'Close' not in data.columns:
            st.error("Failed to load valid market data.")
        else:
            st.success("✅ Data loaded.")
            signal, price, ma20, ma50, rsi, full_data = generate_signals(data)

            st.subheader(f"Latest price for `{symbol}`: ${price:.2f}" if not pd.isna(price) else f"Price data unavailable for {symbol}")
            st.markdown(f"### 🔔 Signal: `{signal}`")
            st.markdown(f"**MA20**: `{ma20:.2f}` | **MA50**: `{ma50:.2f}` | **RSI**: `{rsi:.2f}`")

            # --- Chart Rendering ---
            if 'Close' in full_data.columns:
                plot_df = pd.DataFrame()
                plot_df['Price'] = full_data['Close']
                plot_df['MA20'] = full_data['MA20']
                plot_df['MA50'] = full_data['MA50']
                plot_df = plot_df.dropna()

                if not plot_df.empty:
                    st.line_chart(plot_df)
                else:
                    st.warning("Not enough data to plot moving averages.")
            else:
                st.warning("Close price data missing. Cannot display chart.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
