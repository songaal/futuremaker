import os
import unittest
from datetime import datetime

from futuremaker import utils
from futuremaker.nexus_mock import Nexus


class TestNexusMock(unittest.TestCase):
    def setUp(self):
        symbol = 'XBTUSD'
        leverage = 1
        candle_limit = 20
        candle_period = '1m'
        self.nexus = Nexus('bitmex', symbol, leverage=leverage, candle_limit=candle_limit, candle_period=candle_period,
                           test_start=datetime(2019,1,24,9,0,0), test_end=datetime(2019,1,24,13,0,0))

    def test_update_candle(self):
        def handle_signal(df, item):
            print(item)

        self.nexus.callback(update_candle=handle_signal)
        utils.test_async(self.nexus.load())
        utils.test_async(self.nexus.start_timer())

    def test_update_position(self):
        def update_position(data):
            print(data)
            # order = self.nexus.api.put_order(1, 3500)
            # print(order)

        self.nexus.update_position = update_position
        utils.test_async(self.nexus.load())

    def test_update_order(self):
        def update_order(data):
            print(data)

        self.nexus.update_order = update_order
        utils.test_async(self.nexus.load())


