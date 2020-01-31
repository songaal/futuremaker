import datetime

import pandas as pd
import pytz

from futuremaker import utils
from futuremaker.barlist import BarList
from futuremaker.log import logger


class CandleHandler(object):

    def __init__(self, api, symbol, period, since=None, _update_notify=None):
        self.api = api
        self.symbol = symbol
        self.period = period
        self.since = since # 첨엔 이전 데이터가 몇개 필요하므로 since를 계산해서 받는다.
        self.history = 100 # 캔들은 100 개 유지한다.
        self.datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        self.candle = None
        # 콜백함수.
        self.update_notify = _update_notify
        self.last_candle = None

    def load(self):
        new_data = self.api.bulk_klines(symbol=self.symbol, timeframe=self.period, since=self.since)
        index_list = []
        data_list = []
        for row in new_data:
            logger.debug('>>> row>>> %s', row)

            index = pd.to_datetime(row[0], unit='ms')
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
        # websocket
        self.api.start_websocket(self.symbol, self.period, self.__update)

    def __update(self, row):
        """
        {
            'e': 'kline',
            'E': 1580446096593,
            's': 'BTCUSDT',
            'k': {
                't': 1580443200000,
                'T': 1580446799999,
                's': 'BTCUSDT',
                'i': '1h',
                'f': 237000198,
                'L': 237013567,
                'o': '9444.69000000',
                'c': '9417.00000000',
                'h': '9448.68000000',
                'l': '9401.23000000',
                'v': '1364.01427200',
                'n': 13370,
                'x': False,
                'q': '12855440.52165322',
                'V': '711.89778400',
                'Q': '6709062.23928203',
                'B': '0'
            }
        }
        """
        candle = row['k']
        # if self.last_candle is None or self.last_candle['t'] == candle['t']:
        #     # 동일시간대면 일단 최신데이터로 간직한다.
        #     self.last_candle = candle
        if self.last_candle is not None and self.last_candle['t'] != candle['t']:
            # last candle로 업데이트하고 notify를 호출하여 전략이 실행되게끔 한다.
            unit_time = self.last_candle['t']
            index = pd.to_datetime(unit_time, unit='ms')
            open = self.last_candle['o']
            high = self.last_candle['h']
            low = self.last_candle['l']
            close = self.last_candle['c']
            volume = self.last_candle['v']
            self.candle.update(index, open, high, low, close, volume)
            self.update_notify(self.candle.df)

        #  일단 최신데이터로 간직한다.
        self.last_candle = candle


