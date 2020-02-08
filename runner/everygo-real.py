import sys
# windows
sys.path.append("c:/python/mymodule")
# linux
sys.path.append("/home/ec2-user/futuremaker")

import asyncio
import os

from bots.everygo import EveryGo
from futuremaker.bot import Bot
from futuremaker.binance_api import BinanceAPI

# binance api key
os.environ['key'] = ""
# binance api secret
os.environ['secret'] = ""
# telegram bot token
os.environ['bot_token'] = ""
# telegram my chat id
os.environ['chat_id'] = ""

algo = EveryGo(base='BTC', quote='USDT', floor_decimals=3, paper=True,
               init_capital=10000, max_budget=1000000, commission_rate=0.1, buy_unit=0.01, buy_delay=1)

real_bot = Bot(BinanceAPI(), symbol='BTCUSDT', candle_limit=10,
               backtest=False, candle_period='1m')

asyncio.run(real_bot.run(algo))
