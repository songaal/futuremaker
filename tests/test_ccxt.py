import asyncio
import unittest
from datetime import datetime

from backtester import data_ingest
from backtester import utils as backtester_utils
from futuremaker.log import logger


class TestCcxt(unittest.TestCase):

    def test_bitmex_ohlcv(self):
        exchange = backtester_utils.ccxt_exchange('bitmex', async=True)
        markets = asyncio.get_event_loop().run_until_complete(exchange.load_markets())
        #exchange, symbols, start_date, end_date, periods
        base_dir, filepath = asyncio.get_event_loop().run_until_complete(
            data_ingest.ingest_data(exchange, 'XBTUSD', datetime(2019,1,1,0,0,0), datetime(2019,1,1,12,0,0), '5m', 12)
        )
        logger.debug('filepath > %s', filepath)
