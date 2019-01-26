import pandas as pd
import unittest


class TestData(unittest.TestCase):

    def test_dataframe(self):
        filepath = '/private/var/folders/z2/556j111n5cq852vwc30pff5r0000gp/T/bitmex/201901240000+0900-201901251200+0900/xbt_usd_1m_20.csv'
        data = pd.read_csv(filepath, index_col='Index', usecols=['Index', 'Open', 'High', 'Low', 'Close', 'Volume'])
        # 조작시작.
        print(data)


