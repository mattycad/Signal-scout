import streamlit as st
import yfinance as yf
import ta
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 5 minutes (300,000 ms)
st_autorefresh(interval=300_000, limit=None, key="datarefresh")

st.set_page_config(page_title="📈 Signal Scout Global", layout="centered")
st.title("📈 Signal Scout Global")
st.write("Analyze real-time global stocks, crypto, commodities, and currencies with Buy/Sell signals and close alerts.")

assets = {
    # UK Stocks
    "AstraZeneca (AZN)": "AZN.L",
    "HSBC Holdings (HSBA)": "HSBA.L",
    "Shell (SHEL)": "SHEL.L",
    "BP (BP)": "BP.L",
    "Unilever (ULVR)": "ULVR.L",
    "Diageo (DGE)": "DGE.L",
    "Tesco (TSCO)": "TSCO.L",
    "GlaxoSmithKline (GSK)": "GSK.L",
    "Barclays (BARC)": "BARC.L",
    "Rolls-Royce (RR)": "RR.L",
    # US Stocks
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Amazon (AMZN)": "AMZN",
    "Alphabet (GOOGL)": "GOOGL",
    "Tesla (TSLA)": "TSLA",
    "NVIDIA (NVDA)": "NVDA",
    "JPMorgan Chase (JPM)": "JPM",
    "Johnson & Johnson (JNJ)": "JNJ",
    "Visa (V)": "V",
    "Walmart (WMT)": "WMT",
    # European Stocks
    "SAP (SAP)": "SAP.DE",
    "Siemens (SIE)": "SIE.DE",
    "LVMH (MC)": "MC.PA",
    "TotalEnergies (TTE)": "TTE.PA",
    "Nestlé (NESN)": "NESN.SW",
    "Roche (ROG)": "ROG.SW",
    "ASML (ASML)": "ASML",
    # Cryptocurrencies
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Cardano (ADA)": "ADA-USD",
    "Solana (SOL)": "SOL-USD",
    "Polygon (MATIC)": "MATIC-USD",
    "Polkadot (DOT)": "DOT-USD",
    "Ripple (XRP)": "XRP-USD",
    "Dogecoin (DOGE)": "DOGE-USD",
    "Litecoin (LTC)": "LTC-USD",
    "Chainlink (LINK)": "LINK-USD",
    "Stellar (XLM)": "XLM-USD",
    "VeChain (VET)": "VET-USD",
    "Tron (TRX)": "TRX-USD",
    "EOS (EOS)": "EOS-USD",
    "Monero (XMR)": "XMR-USD",
    "Bitcoin Cash (BCH)": "BCH-USD",
    # Commodities
    "Gold (GC=F)": "GC=F",
    "Silver (SI=F)": "SI=F",
    "Platinum (PL=F)": "PL=F",
    "Palladium (PA=F)": "PA=F",
    "Crude Oil WTI (CL=F)": "CL=F",
    "Brent Crude (BZ=F)": "BZ=F",
    "Natural Gas (NG=F)": "NG=F",
    "Copper (HG=F)": "HG=F",
    "Corn (ZC=F)": "ZC=F",
    "Soybeans (ZS=F)": "ZS=F",
    "Wheat (ZW=F)": "ZW=F",
    "Sugar (SB=F)": "SB=F",
    "Coffee (KC=F)": "KC=F",
    # Currencies (Forex pairs)
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "USD/CHF": "CHF=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X"
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
    close = df["Close"].squeeze()
    if close.ndim != 1:
        close = close.iloc[:, 0]
    rsi = ta.momentum.RSIIndicator(close).rsi()
    sma20 = ta.trend.SMAIndicator(close, window=20).sma_indicator()
    macd_obj = ta.trend.MACD(close)
    macd = macd_obj.macd()
    macd_signal = macd_obj.macd_signal()

    latest = df.iloc[-1]
    rsi_val = float(rsi.iloc[-1])
    sma_val = float(sma20.iloc[-1])
    macd_val = float(macd.iloc[-1])
    macd_signal_val = float(macd_signal.iloc[-1])
    close_val = float(latest["Close"])

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

if "signals" not in st.session_state:
    st.session_state.signals = {}

try:
    df = get_data(ticker)
    signal, reason, rsi_val, sma_val, macd_val, macd_signal_val, close_val = calculate_signal(df, logic_mode)

    st.markdown("---")
    st.subheader(f"📊 {selected_asset} Technical Summary")
    st.metric("Latest Price", f"${close_val:.4f}" if "/" in selected_asset else f"${close_val:.2f}")
    st.write(f"📉 RSI: **{rsi_val:.2f}**")
    st.write(f"📈 SMA (20): **{sma_val:.2f}**")
    st.write(f"📊 MACD: **{macd_val:.2f}** | Signal: **{macd_signal_val:.2f}**")

    color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}

    # Show only BUY or SELL, no HOLD
    if signal == "BUY" or signal == "SELL":
        st.markdown(f"### Signal: {color[signal]} **{signal}**")
        if reason:
            st.caption(f"📌 Reason: {reason}")
    else:
        st.markdown("### Signal: 🟡 **No actionable BUY/SELL signal**")

    st.markdown("---")

    prev_signal = st.session_state.signals.get(selected_asset, None)
    st.session_state.signals[selected_asset] = signal

    # Close position alert if signal flips
    if prev_signal:
        if prev_signal == "BUY" and signal == "SELL":
            st.warning(f"⚠️ Close your BUY position in **{selected_asset}** — signal changed to SELL.")
        elif prev_signal == "SELL" and signal == "BUY":
            st.warning(f"⚠️ Close your SELL position in **{selected_asset}** — signal changed to BUY.")

    st.subheader("🚀 Best Assets to Buy Now")
    best_buys = []
    best_sells = []

    for name, sym in assets.items():
        try:
            data = get_data(sym)
            sig, _, _, _, _, _, price = calculate_signal(data, logic_mode)
            if sig == "BUY":
                best_buys.append((name, price))
            elif sig == "SELL":
                best_sells.append((name, price))
        except Exception:
            continue

    if best_buys:
        for asset_name, price in best_buys:
            st.write(f"🟢 **{asset_name}** at ${price:.2f}")
    else:
        st.write("No BUY signals found right now.")

    st.markdown("---")
    st.subheader("⚠️ Best Assets to Sell Now")
    if best_sells:
        for asset_name, price in best_sells:
            st.write(f"🔴 **{asset_name}** at ${price:.2f}")
    else:
        st.write("No SELL signals found right now.")

except Exception as e:
    st.error(f"❌ Something went wrong while analyzing data: {e}")
