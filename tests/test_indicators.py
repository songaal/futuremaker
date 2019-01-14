import unittest
import numpy as np
import pandas as pd

from futuremaker import indicators


class TestIndicators(unittest.TestCase):

    def test_bbands(self):
        a = [i for i in range(1, 20+1)]
        na = np.asanyarray(a)
        print(na)
        pa = pd.Series(na)
        na2 = pa.values
        print(id(na) == id(na2))
        m, u, l = indicators.bollinger_bands(pd.Series(na), n=5)
        print(m, u, l)
