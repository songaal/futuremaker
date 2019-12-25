import bybit
import pprint
import pandas as pd
import numpy as np

client = bybit.bybit(test=True, api_key="", api_secret="")
print(client.Symbol.Symbol_get().result()[0]["result"][0])

kline_get_kwargs = {
    'symbol': 'BTCUSD',
    'interval': 'D',
    'from': '1572231328',
}
a = client.Kline.Kline_get(**kline_get_kwargs).result()
print(a)
list = a[0]['result']
df = pd.DataFrame(list, columns=['open_time', 'open', 'close', 'high', 'low', 'volume'])
print(df.tail())
df['open_time'] = df['open_time'].astype(int)
df['open'] = df['open'].astype(float)
df['close'] = df['close'].astype(float)
df['high'] = df['high'].astype(float)
df['low'] = df['low'].astype(float)
df['volume'] = df['volume'].astype(float)

df['range'] = (df['high'] - df['low']) * 0.5
df['range_shift1'] = df['range'].shift(1)
df['target'] = df['open'] + df['range_shift1']


df['ror'] = np.where(df['high'] > df['target'], df['close'] / df['target'], 1)
df['cumprod'] = df['ror'].cumprod()
print(df.to_string())
