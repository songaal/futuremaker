import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


filepath = '../../candle_data/BINANCE_BTCUSDT, 60.csv'

df = pd.read_csv(filepath, index_col='time',
                 usecols=['time', 'open', 'high', 'low', 'close', 'volume'],
                 parse_dates=['time'],
                 date_parser=lambda epoch: pd.to_datetime(epoch, unit='s')
                 )

print(df)



fig = plt.figure(figsize=(8, 5))
fig.set_facecolor('w')
gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
axes = []
axes.append(plt.subplot(gs[0]))
axes.append(plt.subplot(gs[1], sharex=axes[0]))
axes[0].get_xaxis().set_visible(False)

from mpl_finance import candlestick_ohlc

x = np.arange(len(df.index))
ohlc = df[['open', 'high', 'low', 'close']].astype(int).values
dohlc = np.hstack((np.reshape(x, (-1, 1)), ohlc))

print(dohlc)
# 봉차트
# candlestick_ohlc(axes[0], dohlc, width=0.5, colorup='r', colordown='b')

# 거래량 차트
# axes[1].bar(x, df.volume, color='k', width=0.6, align='center')
#
# import datetime
# _xticks = []
# _xlabels = []
# _wd_prev = 0
# for _x, d in zip(x, df.date.values):
#     weekday = datetime.datetime.strptime(str(d), '%Y%m%d').weekday()
#     if weekday <= _wd_prev:
#         _xticks.append(_x)
#         _xlabels.append(datetime.datetime.strptime(str(d), '%Y%m%d').strftime('%m/%d'))
#     _wd_prev = weekday
# axes[1].set_xticks(_xticks)
# axes[1].set_xticklabels(_xlabels, rotation=45, minor=False)
#
# # MDD 그리기
# # axes[0].plot(mdd[:2], df.loc[mdd[:2], 'close'], 'k')
#
plt.tight_layout()
plt.show()