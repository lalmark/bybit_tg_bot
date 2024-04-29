from config import api_k, api_sec
from pybit.unified_trading import HTTP
import talib
import numpy as np
import pandas as pd

session = HTTP(api_key=api_k, api_secret=api_sec)

def get_data(kline_time, symbol):
    response = session.get_kline(
        category="spot",
        symbol=symbol,
        interval=kline_time,
        limit=1000
    )

    klines = response.get("result", {}).get('list', [])
    klines = sorted(klines, key=lambda x: int(x[0]))

    columns = ['Date', 'Open', 'Highest', 'Lowest', 'Close', 'Trade volume', 'Turnover']

    # Создание DataFrame
    data = pd.DataFrame(klines, columns=columns)

    return data


def Boll(data):
    data['sma'] = data['Close'].rolling(window=20).mean()
    data['stdev'] = data['Close'].rolling(window=20).std()
    data['Upper'] = data['sma'] + 2 * data['stdev']
    data['lower'] = data['sma'] - 2 * data['stdev']

    return data


def rsi(data):
   rsi_len = 14
   rsi_list = []
   close_prices = data['Close'].values

   close_price = np.array(close_prices, dtype="float")
   #### RSI_1
   rsi_value1 = talib.RSI(close_price, timeperiod=rsi_len)[-1]
   #### RSI_2
   close_price1 = close_price[:-1]
   rsi_value2 = talib.RSI(close_price1, timeperiod=rsi_len)[-1]
   #### RSI_3
   close_price2 = close_price[:-2]
   rsi_value3 = talib.RSI(close_price2, timeperiod=rsi_len)[-1]

   rsi_list.extend([rsi_value3, rsi_value2, rsi_value1])

   return rsi_list


def stratege(data, rsi_data):

    if float(data['Open'].iloc[-1]) <= float(data['lower'].iloc[-1]) and rsi_data[1] < rsi_data[2]:
        print("--------+++++ Сигнал на long +++++-----------")
        return "--------+++++ Сигнал на long +++++-----------" + "\n|Цена открытия  - " + data['Open'].iloc[-1] + "\n|Цена закрытия - " + data['Close'].iloc[-1]

    elif float(data['Close'].iloc[-1]) >= float(data['Upper'].iloc[-1]) and rsi_data[1] > rsi_data[2]:
        print("--------+++++ Сигнал на short +++++-----------")
        return "--------+++++ Сигнал на short +++++-----------" + "\n|Цена открытия  - " + data['Open'].iloc[-1] + "\n|Цена закрытия - " + data['Close'].iloc[-1]

    return 0

def trade_bot(kline_time, symbol):

    print(symbol + " " + kline_time)
    data = get_data(kline_time, symbol)
    data = Boll(data)
    rsi_data = rsi(data)
    data['Date'] = pd.to_datetime(np.int64(data['Date']), unit='ms')
    print(data[['Date', 'Open', 'Close', 'Upper', 'lower']])
    print(rsi_data)
    result = stratege(data, rsi_data)
    return result, data['Date'].iloc[-1]


#print(trade_bot("5", "ETHUSD"))

