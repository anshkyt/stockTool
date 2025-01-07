from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

API_KEY = ""
BASE_URL = "https://www.alphavantage.co/query"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stock/<symbol>", methods=["GET"])
def get_stock_data(symbol):
    rsi_data = fetch_rsi(symbol)
    if rsi_data:
        latest_rsi = get_latest_rsi(rsi_data)
        recommendation = give_recommendation(latest_rsi) if latest_rsi is not None else None
    else:
        return jsonify({"error": "Unable to fetch RSI data"}), 500

    daily_data = fetch_daily_high_low(symbol)
    if daily_data:
        weekly_data = get_weekly_high_low(daily_data)
    else:
        return jsonify({"error": "Unable to fetch daily high/low data"}), 500

    response_data = {
        "rsi": {
            "latest_rsi": latest_rsi,
            "recommendation": recommendation,
        },
        "daily": [
            {
                "date": date,
                "high": high,
                "low": low,
                "average": average,
                "percent_change": percent_change,
            }
            for date, high, low, average, percent_change in weekly_data
        ],
    }
    return jsonify(response_data)

def fetch_rsi(symbol, interval="daily", time_period=14, series_type="close"):
    params = {
        "function": "RSI",
        "symbol": symbol,
        "interval": interval,
        "time_period": time_period,
        "series_type": series_type,
        "apikey": API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    return data.get("Technical Analysis: RSI")

def get_latest_rsi(rsi_data):
    latest_date = max(rsi_data.keys())
    return float(rsi_data[latest_date]["RSI"])

def give_recommendation(rsi):
    if rsi < 30:
        return "Buy (Oversold)"
    elif rsi > 70:
        return "Sell (Overbought)"
    return "Hold (Neutral)"

def fetch_daily_high_low(symbol):
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    return data.get("Time Series (Daily)")

def get_weekly_high_low(daily_data):
    today = datetime.now()
    last_week_dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    weekly_data = []
    previous_high = None
    for date in last_week_dates:
        if date in daily_data:
            high = float(daily_data[date]["2. high"])
            low = float(daily_data[date]["3. low"])
            average = (high + low) / 2
            percent_change = ((high - previous_high) / previous_high) * 100 if previous_high else None
            weekly_data.append((date, high, low, average, percent_change))
            previous_high = high
    return weekly_data

if __name__ == "__main__":
    app.run(debug=True)
