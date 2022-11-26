import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import api_key
import nations
import json
from datetime import date
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
from plotly import graph_objs as go

API_KEY = '6093f76f1a9a4426a7126152b81540df'
nations = nations.countries

def isLeapYear(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def todayStockPrice():
    todayData = {'Current Price': [selection.info['currentPrice']],
            'Previous Close': [selection.info['previousClose']],
            'Open': [selection.info['open']],
            'Lowest Price of the Day': [selection.info['dayLow']],
            'Highest Price of the Day': [selection.info['dayHigh']]
            }
    df = pd.DataFrame(todayData)
    col1, col2 = st.columns(2)
    changePriceToday = selection.info['currentPrice'] - selection.info['open']
    col1.metric(label = "Current Price, Change with regards to Opening Price", value = "%0.2f" % selection.info['currentPrice'], delta = "%0.2f" % changePriceToday)
    changePriceYesterday = data['Close'][len(data) - 1] - data['Close'][len(data) - 2] if len(data) >= 2 else 0
    col2.metric(label = "Previous Closing Price, Previous Day's Price Change", value = "0.2f" % data['Close'][len(data) - 1], delta = "$0.2f" % changePriceYesterday)
    st.dataframe(df)

@st.cache
def load_data(ticker):
    historic_data = yf.download(ticker, START, TODAY)
    historic_data.reset_index(inplace = True)
    return historic_data

def plot_raw_data():
    figure = go.Figure()
    figure.add_trace(go.Scatter(x = data['Date'], y = data['Open'], name = "stock_open"))
    figure.add_trace(go.Scatter(x = data['Date'], y = data['Close'], name = "stock_close"))
    figure.layout.update(title_text = "Data with Slider", xaxis_rangeslider_visible = True)
    st.plotly_chart(figure)
    figure = go.Figure()
    five_days = data.tail(10)
    figure.add_trace(go.Candlestick(x = five_days['Date'], open = five_days['Open'], high = five_days['High'],
                                    low = five_days['Low'],
                                    close = five_days['Close']))
    figure.layout.update(title_text = 'Candle Stick Chart: Trend of the last 10 days', xaxis_rangeslider_visible = True)
    st.plotly_chart(figure)

def historicalTrends():
    st.info(selection.info['longBusinessSummary'])
    st.subheader('Today')
    st.write(data.tail())

def prediction():
    period = 0
    n_years = st.slider('Number of years to predict into:', 1, 4)
    for i in range(0, n_years):
        if isLeapYear(year + i):
            period += 366
        else:
            period += 365

    df_train = data[['Date', 'Close']]
    df_train = df_train.rename(columns = {"Date": "ds", "Close": "y"})
    model_parameters = {
        "daily_seasonality": False,
        "weekly_seasonality": False,
        "yearly_seasonality": True,
        "seasonality_mode": "multiplicative",
        "growth": "logistic"
    }
    pr = Prophet(**model_parameters)
    pr = pr.add_seasonality(name = "monthly", period = 30, fourier_order = 10)
    pr = pr.add_seasonality(name = "quarterly", period = 92.25, fourier_order = 10)
    df_train['cap'] = df_train["y"].max() + df_train["y"].std() * 0.05
    pr.fit(df_train)
    future = pr.make_future_dataframe(periods = period)
    future['cap'] = df_train['cap'].max()
    predictions = pr.predict(future)
    st.subheader('Forecasted Data')
    st.write(predictions)
    st.write(f'Forecast Plot for {n_years} Years')
    prediction_figure1 = plot_plotly(pr, predictions)
    st.plotly_chart(prediction_figure1)
    st.write("Forecast: Yearly, Montly, Quarterly Trends")
    prediction_figure2 = pr.plot_components(predictions)
    st.write(prediction_figure2)

def sideBarHelper(text):
    st.sidebar.text(text)

def sideBarContents():
    st.sidebar.image(selection.info['logo_url'])
    st.sidebar.header(selection.info['shortName'])
    sideBarHelper("Sector: " + selection.info['sector'])
    sideBarHelper("Financial Currency: " + selection.info['financialCurrency'])
    sideBarHelper("Exchange: " + selection.info['exchange'])
    sideBarHelper("Timezone: " + selection.info['exchangeTimezoneName'])

def business_news_feed():

    select_nation = st.sidebar.selectbox("Select Nation: ", nations.keys())
    st.header("FINANCIAL NEWS FEED")
    r = requests.get("https://newsapi.org/v2/top-headlines?country=" + nations[select_nation] + '&category=business&apikey=' + API_KEY)
    business_news = json.loads(r.content)
    length = min(15, len(business_news['articles']))
    for i in range(length):
        news = business_news['articles'][i]['title']
        st.subheader(news)
        image = business_news['articles'][i]['urlToImage']
        try:
            st.image(image)
        except:
            pass
        else:
            pass

        content = business_news['articles'][i]['content']
        st.write(content)
        url = business_news['articles'][i]['url']
        st.write(url)

START = "2015-01-01"
TODAY = date.today().strftime("%Y-%m-%d")
year = int(TODAY[: 4])

st.title('Diverge')

try:
    options = st.sidebar.selectbox("Select Dashboard:", ('Historical Trends', 'Predict Stock Prices', 'Hot-Selling Business News'),
                                   0)
    stock = st.sidebar.text_input("Symbol", value = "AAPL")
    selected_stock = stock
    data = load_data(selected_stock)
    selection = yf.Ticker(selected_stock)

    if options == "Historical Trends":
        company_name = selection.info['longName']
        st.subheader(company_name + "'s Stocks")
        sideBarContents()
        historicalTrends()
        plot_raw_data()

    if options == "Predict Stock Prices":
        company_name = selection.info['longName']
        st.subheader(company_name + "'s Stocks")
        sideBarContents()
        prediction()

    if options == "Hot-Selling Business News":
        business_news_feed()
except KeyError:
    st.error("This company isn't listed on Diverge.")
except FileNotFoundError:
    st.error("There isn't data available on the stock you've chosen!")
except TypeError:
    st.error("There isn't data available on the stock you've chosen!")
except ValueError:
    st.error("Enter a stock symbol!")
except ConnectionError:
    st.error("Connect to the Internet!")






