import asyncio
import unittest
from datetime import datetime

from futuremaker import data_ingest, utils
from futuremaker.log import logger


class TestCcxt(unittest.TestCase):

    def test_bitmex_data_ingest(self):
        exchange = utils.ccxt_exchange('bitmex', async=True)
        markets = asyncio.get_event_loop().run_until_complete(exchange.load_markets())
        #exchange, symbols, start_date, end_date, periods
        base_dir, filepath = asyncio.get_event_loop().run_until_complete(
            data_ingest.ingest_data(exchange, 'XBT/USD', datetime(2019,1,1,0,0,0), datetime(2019,1,1,12,0,0), '5m', 12)
        )
        logger.debug('filepath > %s', filepath)

    def test_ohlcv(self):
        api = utils.ccxt_exchange('bitmex', async=True)

        async def go(symbol, timeframe, limit):
            m = await api.load_markets()
            new_data = await api.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
            print(new_data)
            await api.close()
        utils.test_async(go('XBT/USD', '1m', 10))

