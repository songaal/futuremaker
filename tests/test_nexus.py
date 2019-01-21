import os
import unittest

import bitmex

from futuremaker import utils
from futuremaker.nexus import Nexus


class TestNexus(unittest.TestCase):
    def setUp(self):
        # testnet songaal
        api_key = '<api_key>'
        api_secret = '<api_secret>'
        testnet = True
        symbol = 'XBTUSD'
        leverage = 1
        candle_limit = 20
        candle_period = '1m'
        self.nexus = Nexus(symbol, leverage=leverage, api_key=api_key, api_secret=api_secret, testnet=testnet, candle_limit=candle_limit, candle_period=candle_period)

    def test_update_candle(self):
        def handle_signal(data):
            print(data)

        self.nexus.update_candle = handle_signal
        utils.test_async(self.nexus.load())

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


