import asyncio
import os

from bots.everygo import EveryGo
from futuremaker.bot import Bot
from futuremaker.binance_api import BinanceAPI

# os.environ['key'] = ""
# os.environ['secret'] = ""
# os.environ['bot_token'] = ""
# os.environ['chat_id'] = ""

algo = EveryGo(base='BTC', quote='USDT', floor_decimals=2, paper=False,
               init_capital=300, max_budget=1000000, commission_rate=0.1, buy_unit=0.01, buy_delay=1)

real_bot = Bot(BinanceAPI(), symbol='BTCUSDT', candle_limit=10,
               backtest=False, candle_period='1m')

asyncio.run(real_bot.run(algo))
