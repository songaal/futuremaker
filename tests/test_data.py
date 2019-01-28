import asyncio
from datetime import datetime, timezone, timedelta

import pandas as pd
import unittest

from futuremaker import utils, indicators
from futuremaker.data_ingest import ingest_data
from futuremaker.indicators import heikinashi
from futuremaker.log import logger
from futuremaker.zigzag import zigzag, zigzag2
import matplotlib.pyplot as plt
import matplotlib.dates as md


class TestData(unittest.TestCase):

    def test_zigzag(self):
        api = utils.ccxt_exchange('bitmex', async=True)
        asyncio.get_event_loop().run_until_complete(api.load_markets())
        _, filepath = asyncio.get_event_loop().run_until_complete(
            ingest_data(api, symbol='XBT/USD',
                        start_date=datetime(2019, 1, 24, 5, 0, 0, tzinfo=timezone(timedelta(hours=9))),
                        end_date=datetime(2019, 1, 26, 19, 59, 59, tzinfo=timezone(timedelta(hours=9))),
                        interval='5m', history=0, reload=False)
        )
        print('filepath > ', filepath)
        data = pd.read_csv(filepath, index_col='Index', parse_dates=True,
                           date_parser=lambda x: datetime.fromtimestamp(int(x) / 1000),
                           usecols=['Index', 'Open', 'High', 'Low', 'Close', 'Volume'])
        # 조작시작.
        # data = data[300:500]
        plt.plot(data.Close)

        # z = zigzag(data, deviation=0.05)
        # plt.plot(z, 'ro')

        zz_high, zz_low = zigzag2(data, deviation=0.03, spread=1)
        plt.plot(zz_high, 'go')
        plt.plot(zz_low, 'ro')

        # 알고리즘.
        # 1. 저점이 올라가면 상승추세. 이전 고점 경신하면
        # 2. 고점이 내려오면 하락추세. 이전 저점 깨지면..

        # prev_high = None
        # my_index = []
        # for i, v in zz_high.items():
        #     # print(i, v, prev_high)
        #     if prev_high is not None:
        #         if v < prev_high:
        #             my_index.append((i, 'D'))
        #     prev_high = v
        #
        # prev_low = None
        # for i, v in zz_low.items():
        #     # print(i, v, prev_low)
        #     if prev_low is not None:
        #         if v > prev_low:
        #             my_index.append((i, 'U'))
        #     prev_low = v
        #
        # my_index.sort()
        #
        # prev_ts = None
        # prev_type = None
        # for tup in my_index:
        #     print(tup)
        #     ts = tup[0]
        #     type = tup[1]
        #
        #     if prev_ts is None and prev_type is None:
        #         prev_ts = ts
        #         prev_type = type
        #     else:
        #         if type != prev_type:
        #             plt.axvspan(prev_ts, ts, facecolor='g' if prev_type == 'U' else 'r', alpha=0.5)
        #             prev_ts = ts
        #             prev_type = type

        # print(my_index)
        ax = plt.gca()
        xfmt = md.DateFormatter('%Y-%m-%d %H:%M:%S')
        ax.xaxis.set_major_formatter(xfmt)
        plt.xticks(rotation=30)
        plt.subplots_adjust(bottom=0.2)
        plt.grid(True)
        fig = plt.gcf()
        fig.set_size_inches(16, 5)
        plt.show()

    def test_heikin(self):
        api = utils.ccxt_exchange('bitmex', async=True)
        asyncio.get_event_loop().run_until_complete(api.load_markets())
        _, filepath = asyncio.get_event_loop().run_until_complete(
            ingest_data(api, symbol='XBT/USD',
                        start_date=datetime(2019, 1, 20, 12, 0, 0, tzinfo=timezone(timedelta(hours=9))),
                        end_date=datetime(2019, 1, 28, 15, 0, 0, tzinfo=timezone(timedelta(hours=9))),
                        interval='1m', history=0, reload=False)
        )
        print('filepath > ', filepath)
        data = pd.read_csv(filepath, index_col='Index', parse_dates=True,
                           date_parser=lambda x: datetime.fromtimestamp(int(x) / 1000),
                           usecols=['Index', 'Open', 'High', 'Low', 'Close', 'Volume'])

        ha = heikinashi(data)

        prev_diff = 0
        trade = 0
        entry_idx = None
        long_entry = None
        short_entry = None
        total_pnl = 0
        r_index = []
        r_value = []
        N = 3 # 3개의 연속 가격을 확인하여 익절.
        for diff, ha_close, close, idx in zip(ha.HA_Diff, ha.HA_Close, data.Close, data.index):
            pnl = 0
            # plt.axvspan(prev_ts, ts, facecolor='g' if prev_type == 'U' else 'r', alpha=0.5)

            # 갯수가 될때까지 기다린다.
            if short_entry is not None:
                # 숏 청산.
                if diff > 0 or self.great_or_eq(ha.HA_Close, N):
                    pnl = short_entry - close
                    total_pnl += pnl
                    elapsed = idx - entry_idx
                    r_index.append(idx)
                    r_value.append(total_pnl)
                    trade += 1
                    logger.info('[%s] TOTAL_PNL[%s] PNL[$%s] SEC[%s] Price[%s->%s] Time[%s~%s]', trade, total_pnl, pnl, elapsed.seconds, short_entry,
                                close, entry_idx, idx)
                    short_entry = None

            elif long_entry is not None:

                if diff < 0 or self.less_or_eq(ha.HA_Close, N):
                    pnl = close - long_entry
                    total_pnl += pnl
                    elapsed = idx - entry_idx
                    r_index.append(idx)
                    r_value.append(total_pnl)
                    trade += 1
                    logger.info('[%s] TOTAL_PNL[%s] PNL[$%s] SEC[%s] Price[%s->%s] Time[%s~%s]', trade, total_pnl, pnl, elapsed.seconds, long_entry,
                                close, entry_idx, idx)
                    long_entry = None

            # 청산하고 바로 다시 진입도 가능하다.
            if long_entry is None and short_entry is None:
                if diff > 0 and prev_diff > 0:
                    # 가격이 높아지는 추세.
                    if prev_diff + diff >= 1:
                        # 롱 진입.
                        long_entry = close
                        entry_idx = idx
                        trade += 1
                elif diff < 0 and prev_diff < 0:
                    # 가격이 낮아지는 추세.
                    if prev_diff + diff <= -1:
                        # 숏 진입.
                        short_entry = close
                        entry_idx = idx
                        trade += 1

            prev_diff = diff

        fig = plt.figure()
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)

        # 차트1
        ax1.plot(data.Close)

        # 차트2
        pnl_series = pd.Series(data=r_value, index=r_index)
        ax2.plot(pnl_series, 'ro')

        ax = plt.gca()
        xfmt = md.DateFormatter('%Y-%m-%d %H:%M:%S')
        ax.xaxis.set_major_formatter(xfmt)
        plt.xticks(rotation=30)
        plt.subplots_adjust(bottom=0.2)
        plt.grid(True)
        fig = plt.gcf()
        fig.set_size_inches(16, 7)
        plt.show()

    def less_or_eq(self, list, size):
        prev_val = None
        for val in list[-size:]:
            if prev_val and val > prev_val:
                return False
            prev_val = val
        return True

    def great_or_eq(self, list, size):
        prev_val = None
        for val in list[-size:]:
            if prev_val and val < prev_val:
                return False
            prev_val = val
        return True
