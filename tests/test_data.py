import asyncio
from datetime import datetime

import pandas as pd
import unittest

from futuremaker import utils
from futuremaker.data_ingest import ingest_data
from futuremaker.zigzag import zigzag, zigzag2
import matplotlib.pyplot as plt


class TestData(unittest.TestCase):

    def test_dataframe(self):
        api = utils.ccxt_exchange('bitmex', async=True)
        asyncio.get_event_loop().run_until_complete(api.load_markets())
        _, filepath = asyncio.get_event_loop().run_until_complete(
            ingest_data(api, symbol='XBT/USD',
                        start_date=datetime(2019, 1, 23, 0, 0, 0),
                        end_date=datetime(2019, 1, 25, 23, 59, 59),
                        interval='1h', history=20, reload=False)
        )
        # filepath = '/private/var/folders/z2/556j111n5cq852vwc30pff5r0000gp/T/bitmex/201901240000+0900-201901251200+0900/xbt_usd_1m_20.csv'
        data = pd.read_csv(filepath, index_col='Index', usecols=['Index', 'Open', 'High', 'Low', 'Close', 'Volume'])
        # 조작시작.
        # data = data[300:500]
        plt.plot(data.Close)

        # z = zigzag(data, deviation=0.05)
        # plt.plot(z, 'ro')

        zz_high, zz_low = zigzag2(data, deviation=0.03)
        plt.plot(zz_high, 'go')
        plt.plot(zz_low, 'ro')

        # 알고리즘.
        # 1. 저점이 올라가면 상승추세. 이전 고점 경신하면
        # 2. 고점이 내려오면 하락추세. 이전 저점 깨지면..

        prev_high = None
        my_index = []
        for i, v in zz_high.items():
            # print(i, v, prev_high)
            if prev_high is not None:
                if v < prev_high:
                    my_index.append((i, 'D'))
            prev_high = v

        prev_low = None
        for i, v in zz_low.items():
            # print(i, v, prev_low)
            if prev_low is not None:
                if v > prev_low:
                    my_index.append((i, 'U'))
            prev_low = v

        my_index.sort()

        prev_ts = None
        prev_type = None
        for tup in my_index:
            print(tup)
            ts = tup[0]
            type = tup[1]

            if prev_ts is None and prev_type is None:
                prev_ts = ts
                prev_type = type
            else:
                if type != prev_type:
                    plt.axvspan(prev_ts, ts, facecolor='g' if prev_type == 'U' else 'r', alpha=0.5)
                    prev_ts = ts
                    prev_type = type

        # print(my_index)
        plt.grid(True)
        fig = plt.gcf()
        fig.set_size_inches(16, 5)
        plt.show()
