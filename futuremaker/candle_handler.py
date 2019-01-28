import datetime

import pandas as pd
import pytz

from futuremaker import utils
from futuremaker.barlist import BarList
from futuremaker.log import logger


class CandleHandler(object):

    def __init__(self, api, symbol, period, history, since=None):
        self.api = api
        self.symbol = symbol
        self.period = period
        self.history = history
        self.since = since
        self.datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'

    async def load(self):
        # 미리 history 크기의 df 를 만들고.
        # history 만큼 캔들 데이터를 채워넣는다.
        # 초기화. 데이터는 비어있음.

        # 최신것부터 limit 개를 가져온다.
        new_data = await self.api.fetch_ohlcv(symbol= self.symbol, timeframe=self.period, since=self.since, limit=self.history)
        # 오래된순 정렬로 바꿈.
        # new_data = new_data[::-1]
        index_list = []
        data_list = []
        for row in new_data:
            logger.info('>>> row>>> %s', row)

            index = row[0]
            index_list.append(index)
            data_list.append({
                'Open': row[1],
                'High': row[2],
                'Low': row[3],
                'Close': row[4],
                'Volume': row[5],
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

