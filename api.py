import yfinance as yf
import requests

def getStock(search_term):
    results = []
    query = requests.get(f'https://yfapi.net/v6/finance/autocomplete?region=IT&lang=en&query={search_term}', 
    headers={
        'accept': 'application/json',
        'X-API-KEY': 'T4VwA9L9In8Nj03jjuocg5y45CUtVuHR9yYcUNJQ'
    })
    response = query.json()
    print(response)
    for i in response['ResultSet']['Result']:
        final = i['symbol']
        results.append(final)

    try:
        stock = yf.Ticker(results[0])
        price = stock.info["regularMarketPrice"]
        full_name = stock.info['longName']
        curreny = stock.info["currency"]
    except Exception as e:
        print('Something went wrong')

    return f"The stock price of {full_name} is {price} {curreny}"



def getChart(name):
    import plotly.graph_objects as go
    import pandas as pd
    from datetime import datetime

    df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv')
    print(df.head)

    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                    open=df['AAPL.Open'],
                    high=df['AAPL.High'],
                    low=df['AAPL.Low'],
                    close=df['AAPL.Close'])])
    fig.show()

def getChart2():
    ##
    # From https://www.learndatasci.com/tutorials/python-finance-part-yahoo-finance-api-pandas-matplotlib/
    ##
    from pandas_datareader import data
    import matplotlib.pyplot as plt
    import pandas as pd
    import plotly.graph_objects as go

    start_date = '2010-01-01'
    end_date = '2016-12-31'

    # User pandas_reader.data.DataReader to load the desired data. As simple as that.
    panel_data = data.DataReader('AMZN', 'yahoo', start_date, end_date)
    print(panel_data.head())
    close = panel_data['Close']

    # Getting all weekdays between 01/01/2000 and 12/31/2016
    all_weekdays = pd.date_range(start=start_date, end=end_date, freq='B')

    # How do we align the existing prices in adj_close with our new set of dates?
    # All we need to do is reindex close using all_weekdays as the new index
    close = close.reindex(all_weekdays)

    # Reindexing will insert missing values (NaN) for the dates that were not present
    # in the original set. To cope with this, we can fill the missing by replacing them
    # with the latest available price for each instrument.
    close = close.fillna(method='ffill')

    # Calculate the 20 and 100 days moving averages of the closing prices
    short_rolling_msft = close.rolling(window=20).mean()

    fig, ax = plt.subplots()
    ax.plot(close.index, close, label='Close price')
    ax.set_xlabel('Date')
    ax.set_ylabel('Closing price ($)')
    ax.set_title("Amazon")
    ax.legend()
    #plt.show()
    #plt.savefig("line.jpg")

    fig = go.Figure(data=[go.Candlestick(x=panel_data.index,
                    open=panel_data['Open'],
                    high=panel_data['High'],
                    low=panel_data['Low'],
                    close=panel_data['Close'])])
    fig.update_layout(
            xaxis_rangeslider_visible=False,
            title=f"Amazon {panel_data.index[0].strftime('%Y/%m/%d')}-{panel_data.index[-1].strftime('%Y/%m/%d')}",
            xaxis_title="Time period",)
    fig.show()
    #fig.write_image("candle.jpeg")


def telegram():
    import telegram
    bot = telegram.Bot(token='5103395629:AAGARYr4hHjM78iqR2R7p-gOpw-ed6K5wtk')
    bot.send_message(chat_id="403864881", text="I'm a bot, please talk to me!")
    bot.send_photo(chat_id="403864881", photo=open('C:/Users/Steve/Pictures/conci.jpg', 'rb'))

#stock = input("Enter the company's name: ")
#final = getStock(stock)
#print(final)

#getChart2()

#getChart("amazon")


##
# Test finance api
##
from actions import finance_api

# company_symbol , ambiguity = finance_api.get_symbol_from_name("amazon", debug=False)
# data = finance_api.get_past_values_from_symbol(company_symbol, debug=True)
# #plot_path = finance_api.create_past_values_plot(data, "Alphabet Inc.", type="line")
# finance_api.predict_trend(data)


# data = finance_api.get_company_news("amazon")
# print(len(data["response"]["results"]))


data = finance_api.get_company_info("amazon")
print(data)