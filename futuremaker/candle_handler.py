import datetime

import pandas as pd
import pytz

from futuremaker import utils
from futuremaker.barlist import BarList
from futuremaker.log import logger


class CandleHandler(object):

    def __init__(self, api, symbol, period, since=None):
        self.api = api
        self.symbol = symbol
        self.period = period
        self.since = since # 첨엔 이전 데이터가 몇개 필요하므로 since를 계산해서 받는다.
        self.history = 100 # 캔들은 100 개 유지한다.
        self.datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        self.candle = None

    # async
    def load(self):
        # 미리 history 크기의 df 를 만들고.
        # history 만큼 캔들 데이터를 채워넣는다.
        # 초기화. 데이터는 비어있음.

        # 최신것부터 limit 개를 가져온다.
        # new_data = await
        new_data = self.api.fetch_ohlcv(symbol= self.symbol, timeframe=self.period, since=self.since)
        # 오래된순 정렬로 바꿈.
        # new_data = new_data[::-1]
        index_list = []
        data_list = []
        for row in new_data:
            logger.debug('>>> row>>> %s', row)

            index = row[0]
            index_list.append(index)
            data_list.append({
                'open': row[1],
                'high': row[2],
                'low': row[3],
                'close': row[4],
                'volume': row[5],
            })

        freq = utils.period_to_freq(self.period)
        self.candle = BarList(self.symbol, self.history, freq)
        self.candle.init(index_list, data_list)

    def update(self, row):
        dt = datetime.datetime.strptime(row['timestamp'], self.datetime_format).replace(tzinfo=pytz.UTC)
        index = dt.timestamp() * 1000
        open = row['open']
        high = row['high']
        low = row['low']
        close = row['close']
        volume = row['volume']
        self.candle.update(index, open, high, low, close, volume)

        return self.candle.df

