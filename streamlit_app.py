import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from ta.momentum import RSIIndicator
from ta.trend import MACD
import matplotlib.pyplot as plt

# --------- UTILS ---------
def load_stock(ticker):
    return yf.Ticker(ticker)

def get_fundamentals(stock):
    info = stock.info
    return {
        "P/E Ratio": info.get("trailingPE"),
        "EPS": info.get("trailingEps"),
        "Debt to Equity": info.get("debtToEquity"),
        "Revenue Growth (YoY)": info.get("revenueGrowth"),
    }

def get_catalysts(stock):
    return [
        "Earnings Date: " + str(stock.calendar.loc['Earnings Date'][0]) if 'Earnings Date' in stock.calendar.index else "No earnings info",
        "Recent News: Check Yahoo Finance",
        "Sector Shifts: Monitor ETF performance in this sector"
    ]

def compare_stocks(stock_a, stock_b):
    data = {}
    for s in [stock_a, stock_b]:
        info = s.info
        data[info["symbol"]] = {
            "P/E": info.get("trailingPE"),
            "EPS": info.get("trailingEps"),
            "Market Cap": info.get("marketCap"),
            "Return on Equity": info.get("returnOnEquity"),
        }
    return pd.DataFrame(data)

def analyst_sentiment(stock):
    recs = stock.recommendations
    if recs is not None and not recs.empty:
        recent = recs.tail(10)
        return recent["To Grade"].value_counts()
    return "No analyst data available."

def support_resistance(data):
    close = data['Close']
    support = close.min()
    resistance = close.max()
    current = close.iloc[-1]
    reward = resistance - current
    risk = current - support
    return support, resistance, risk, reward

def swing_trading_signals(data):
    close = data['Close']
    rsi = RSIIndicator(close).rsi()
    macd = MACD(close).macd_diff()
    sma_50 = close.rolling(window=50).mean()
    sma_200 = close.rolling(window=200).mean()
    return rsi, macd, sma_50, sma_200

# --------- STREAMLIT UI ---------
st.title("📊 Stock Analyst Pro")

menu = st.sidebar.selectbox("Choose Feature", [
    "1. Fundamentals",
    "2. Catalysts (Next 30 Days)",
    "3. Compare Stocks",
    "4. Analyst Sentiment",
    "5. Risk/Reward (Support/Resistance)",
    "6. Portfolio Tracker",
    "7. Swing Trading Plan"
])

if menu == "1. Fundamentals":
    ticker = st.text_input("Enter stock ticker")
    if ticker:
        stock = load_stock(ticker)
        fundamentals = get_fundamentals(stock)
        st.subheader("Key Fundamentals")
        st.json(fundamentals)

elif menu == "2. Catalysts (Next 30 Days)":
    ticker = st.text_input("Enter stock ticker")
    if ticker:
        stock = load_stock(ticker)
        st.subheader("Potential Catalysts")
        for c in get_catalysts(stock):
            st.write("- " + c)

elif menu == "3. Compare Stocks":
    t1 = st.text_input("Stock A")
    t2 = st.text_input("Stock B")
    if t1 and t2:
        s1, s2 = load_stock(t1), load_stock(t2)
        df = compare_stocks(s1, s2)
        st.dataframe(df)

elif menu == "4. Analyst Sentiment":
    ticker = st.text_input("Enter stock ticker")
    if ticker:
        stock = load_stock(ticker)
        sentiment = analyst_sentiment(stock)
        st.subheader("Analyst Sentiment")
        st.write(sentiment)

elif menu == "5. Risk/Reward (Support/Resistance)":
    ticker = st.text_input("Enter stock ticker")
    if ticker:
        stock = load_stock(ticker)
        hist = stock.history(period="6mo")
        s, r, risk, reward = support_resistance(hist)
        st.subheader("Support/Resistance Levels")
        st.write(f"Support: {s:.2f} | Resistance: {r:.2f}")
        st.write(f"Risk: {risk:.2f} | Reward: {reward:.2f}")
        st.write(f"Risk/Reward Ratio: {reward/risk:.2f}" if risk != 0 else "Invalid Risk Value")

elif menu == "6. Portfolio Tracker":
    tickers = st.text_input("Enter portfolio tickers (comma-separated)").upper().split(",")
    weights = st.text_input("Enter portfolio weights (comma-separated)").split(",")
    if tickers and weights and len(tickers) == len(weights):
        weights = list(map(float, weights))
        data = {}
        for i, t in enumerate(tickers):
            stock = load_stock(t.strip())
            price = stock.history(period="1mo")['Close']
            data[t] = price.pct_change().dropna()
        df = pd.DataFrame(data)
        perf = df.mean() * 100
        portfolio_return = np.dot(perf, weights)
        st.subheader("Portfolio Performance")
        st.write(f"Weighted Return (1M): {portfolio_return:.2f}%")
        st.bar_chart(perf)

elif menu == "7. Swing Trading Plan":
    ticker = st.text_input("Enter stock ticker")
    if ticker:
        stock = load_stock(ticker)
        hist = stock.history(period="6mo")
        rsi, macd, sma_50, sma_200 = swing_trading_signals(hist)
        st.subheader("Indicators")
        st.line_chart(pd.DataFrame({
            "Price": hist['Close'],
            "50 SMA": sma_50,
            "200 SMA": sma_200
        }))
        st.line_chart(pd.DataFrame({
            "RSI": rsi,
            "MACD": macd
        }))
        st.write("📈 RSI < 30: Oversold | RSI > 70: Overbought")
        st.write("📉 MACD crossover can indicate momentum change.")
