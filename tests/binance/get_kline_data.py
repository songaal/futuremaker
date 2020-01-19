#pip install python-binance
import pandas as pd
from binance.client import Client
client = Client()

# get market depth
# depth = client.get_order_book(symbol='BNBBTC')

# fetch 1 minute klines for the last day up until now
# klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_5MINUTE, "90 day ago UTC", limit=1000)
klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1DAY, "2018-01-18", limit=1000)

print(klines)
df = pd.DataFrame(klines, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'volume', 'trades', 'taker_buy_base_volume', 'taker_buy_quote_volume','ignore'])
print(df.tail())
# df['open_time'] = df['open_time'].astype(int)
df['date'] = pd.to_datetime(df['open_time'], unit='ms')
# df['open'] = df['open'].astype(float)
# df['high'] = df['high'].astype(float)
# df['low'] = df['low'].astype(float)
# df['close'] = df['close'].astype(float)
# df['volume'] = df['volume'].astype(float)
#
df.to_csv('d2.csv', mode='w')
print('Done')
