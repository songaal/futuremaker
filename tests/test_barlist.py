import unittest
from random import uniform

import pandas as pd

from futuremaker.barlist import BarList


class TestBarlist(unittest.TestCase):
    def setUp(self):
        pass

    def test_create(self):
        barlist = BarList('XBT', '1m', 4)
        for i in range(10):
            timestamp = 1547210853 + i  * 60
            open = uniform(4000, 4010)
            close = uniform(4000, 4010)
            high = uniform(max([open, close]), 4010)
            low = uniform(4000, min([open, close]))
            volume = 50000 + 1 * 10
            barlist.update(timestamp, open, high, low, close, volume)

        # print(barlist)

    def dataframe_groupby(self):

        newCandleSize = 5
        # Create the new DataFrame
        dfOrig = pd.DataFrame()
        df = pd.DataFrame()

        # subsample to get the opening values
        df['open'] = dfOrig['open'].iloc[::newCandleSize]

        # generate artificial groups to get the high and low
        tmpRange = pd.np.arange(len(dfOrig)) // newCandleSize
        df['high'] = dfOrig['high'].groupby(tmpRange).max()
        df['low'] = dfOrig['low'].groupby(tmpRange).min()

        # subsample to get the closing values
        df['close'] = dfOrig['close'].iloc[newCandleSize - 1::newCandleSize]

        # generate artificial groups to get the vol
        df['vol'] = dfOrig['vol'].groupby(tmpRange).sum()
