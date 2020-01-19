import bybit
import pprint
import pandas as pd
import numpy as np
import datetime
interval = '5'
client = bybit.bybit(test=True, api_key="", api_secret="")
print(client.Symbol.Symbol_get().result()[0]["result"][0])

kline_get_kwargs = {
    'symbol': 'BTCUSD',
    'interval': interval,
    'from': '1561986000',
#     2019.10.1 >> 1569934800
#     2019.7.1 >> 1561986000
}
a = client.Kline.Kline_get(**kline_get_kwargs).result()
print(a)
list = a[0]['result']
df = pd.DataFrame(list, columns=['open_time', 'open', 'close', 'high', 'low', 'volume'])
print(df.tail())
df['open_time'] = df['open_time'].astype(int)
df['date'] = pd.to_datetime(df['open_time'], unit='s')
df['open'] = df['open'].astype(float)
df['high'] = df['high'].astype(float)
df['low'] = df['low'].astype(float)
df['close'] = df['close'].astype(float)
df['volume'] = df['volume'].astype(float)

df.to_csv(interval + '.csv', mode='w')
print('Done')
