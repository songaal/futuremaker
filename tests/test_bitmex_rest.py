import unittest

from time import sleep
from futuremaker.log import logger
import bitmex

class TestBitmexREST(unittest.TestCase):
    def setUp(self):
        self.symbol = "XBTUSD"
        self.api_key = 'AGtODupchqfoF2c7MJGCrZ2_'
        self.api_secret = 'wg8Rr54R7c4yJMmTT50gVGS7LkvtdXaA-1IH0286CDGrEQfT'

    def test_order(self):
        client = bitmex.bitmex(test=True, api_key=self.api_key, api_secret=self.api_secret)
        result = client.Order.Order_new(symbol="XBTUSD", ordType='Limit', orderQty=1, price=3691,
                                        execInst='ParticipateDoNotInitiate', text='BB_LONG').result()

        order = result[0]
        order_id = order['orderID']
        order_status = order['ordStatus'] # Canceled
        print(f'order_id[{order_id}] status[{order_status}]')
        print(result)

    def test_candle_history(self):
        client = bitmex.bitmex(test=True)
        result = client.Trade.Trade_getBucketed(symbol="XBTUSD", reverse=True, count=3, binSize='1m').result()
        print(result)

