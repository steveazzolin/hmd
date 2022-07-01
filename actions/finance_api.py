from locale import currency
import yfinance as yf
import requests
import telegram

from pandas_datareader import data

import matplotlib.pyplot as plt    
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import numpy as np

from actions.api_keys import *


"""
TODO:
    - Ask the user the first time that want a plot sent whether it wants a candle/line plot and save the result for next queries
    - Ask the user the period of the plot
"""

def get_symbol_from_name(name, debug=False):
    """
        Return symbol corresponding to company name
        ret:
            first symbol retireved from API
            boolean indicating whether there were multiple symbols associated to the company name
    """
    results = []
    query = requests.get(f'https://yfapi.net/v6/finance/autocomplete?region=IT&lang=en&query={name}', 
    headers={
        'accept': 'application/json',
        'X-API-KEY': YAHOO_API_KEYS
    })
    response = query.json()
    if debug:
        print(response)
    for i in response['ResultSet']['Result']:
        final = i['symbol']
        results.append(final)
    return results[0] , len(results) == 1


def get_value_from_symbol(symbol, debug=False):
    try:
        stock = yf.Ticker(symbol)
        price = stock.info["regularMarketPrice"]
        full_name = stock.info['longName']
        currency = stock.info["currency"]
    except Exception as e:
        print('Something went wrong')
    print("Full name = ", full_name)
    return price, full_name, currency
    
def get_past_values_from_symbol(symbol, debug=False, start_date=None, end_date=None):
    try:
        if start_date is None:
            start_date = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.today().strftime('%Y-%m-%d')

        panel_data = data.DataReader(symbol, 'yahoo', start_date, end_date)
        if debug:
            print(panel_data.head())
    except Exception as e:
        print('Something went wrong')
    return panel_data

def create_past_values_plot(data, company_name, type):
    path = "plots/plot.jpeg"
    title = f"{company_name.upper()} {data.index[0].strftime('%Y/%m/%d')}-{data.index[-1].strftime('%Y/%m/%d')}"
    xlabel = "Time period"
    if type == "candle":
        fig = go.Figure(
            data=[go.Candlestick(x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'])])
        fig.update_layout(
            xaxis_rangeslider_visible=False,
            title=title,
            xaxis_title=xlabel,
            yaxis_title="$")
        fig.write_image(path)
    elif type == "line":
        fig, ax = plt.subplots(figsize=(8, 9))
        ax.plot(data.Close.index, data.Close, label='Closing price')
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Closing price ($)')
        ax.set_title(title)
        ax.tick_params(axis='x', labelrotation = 45)
        ax.legend()
        plt.savefig(path)
    else:
        raise ValueError("type value not known: ", type)
    return path

def send_plot_telegram(plot_path, message=None, chat_id="403864881"):
    bot = telegram.Bot(token=TELEGRAM_API_KEY)
    if message is not None:
        bot.send_message(chat_id=chat_id, text=message)
    bot.send_photo(chat_id=chat_id, photo=open(plot_path, 'rb'))


def predict_trend(data, debug=False):
    """
    Return an positive/negative int with the degree of rise/fall
    Values > 0 indicate a positive trend, while < 0 a negative trend
    """
    y = data['Close'].to_numpy()
    regressor = LinearRegression(normalize=True).fit(np.arange(len(y)).reshape(len(y), -1), y.reshape(len(y), -1))

    if debug:
        fig , ax = plt.subplots(figsize=(8, 9))
        ax.plot(data.Close.index, data.Close, label='Closing price')
        ax.set_ylabel('Closing price ($)')
        ax.set_title("Regression line test")
        ax.plot(data.Close.index, regressor.predict(np.arange(len(y)).reshape(len(y), -1)))
        ax.tick_params(axis='x', labelrotation = 45)
        ax.legend()
        plt.savefig("plots/debug_predict_trend.jpeg")
    return regressor.coef_