import time

from bots.test import AlertGo

algo = AlertGo(base='BTC', quote='USDT', floor_decimals=3, init_capital=10000, max_budget=1000000)
algo.load_status()
time.sleep(0.3)
algo.save_status()
# time.sleep(1)
trade = {
    "tradeTime": "<timestamp10>",
    "datetime": "2020-01-12T00:00:00",
    "symbol": "BTC/USDT",
    "action": "SELL",
    "position": "SHORT",
    "price": 9010.5,
    "quantity": 1.22
}
algo.append_trade(trade)
