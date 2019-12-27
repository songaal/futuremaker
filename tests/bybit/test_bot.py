import bybit
import pprint
import pandas as pd
import numpy as np
import datetime

import pandas as pd
# df = pd.read_csv('90d.csv')
df = pd.read_csv('6M.csv')

df['range'] = (df['high'] - df['low']) * 0.5
df['range_shift1'] = df['range'].shift(1)
df['long_target'] = df['open'] + df['range_shift1']
df['short_target'] = df['open'] + df['range_shift1']

df['close-open'] = df['close'] - df['open']

# 양봉인지 여부.
df['is_green'] = df['close-open'] >= 0


def long_sell_price(x):
    if x['is_green']:
        # 오름봉이면, 최대값에서 100불이 빠졌을때 익절한다.
        return x['high'] - 100 if x['close'] <= x['high'] - 100 else x['close']
    else:
        # 내린봉이면. low 가 진입가보다 -30불이상 더 낮으면 손절한다.
        return x['long_target'] - 30 if x['low'] <= x['long_target'] - 30 else x['close']


def short_sell_price(x):
    if not x['is_green']:
        # 내림봉이면 익절, 최대값에서 100불이 빠졌을때 익절한다.
        return x['low'] + 100 if x['close'] >= x['low'] + 100 else x['close']
    else:
        # 오름봉이면 손절. low 가 진입가보다 -30불이상 더 낮으면 손절한다.
        return x['short_target'] + 30 if x['high'] >= x['short_target'] + 30 else x['close']


# 롱타겟
# df['high'] > df['long_target'
df['sell_price'] = df.apply(lambda x: long_sell_price(x), axis=1)
df['ror'] = np.where(df['high'] > df['long_target'], df['sell_price'] / df['long_target'], 1)
df['pnl'] = df['sell_price'] - df['long_target']
df['profit%'] = df['pnl'] / df['long_target']

# 숏타켓
# df['low'] < df['short_target']
df['sell_price'] = df.apply(lambda x: short_sell_price(x), axis=1)
df['ror'] = np.where(df['low'] < df['short_target'], df['short_target'] / df['sell_price'], 1)
df['pnl'] = df['short_target'] - df['sell_price']
df['profit%'] = df['pnl'] / df['short_target']



df['cumprod'] = df['ror'].cumprod()

print(df[['date', 'open', 'high', 'long_target', 'short_price', 'close', 'sell_price', 'profit%', 'pnl', 'ror', 'cumprod']].to_string())
