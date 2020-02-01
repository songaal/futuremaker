import time
import os
from futuremaker.binance_api import BinanceAPI

symbol = 'BTCUSDT'
api = BinanceAPI()


def loan_test():
    # asset = 'USDT'
    asset = 'BTC'
    amount = 0.003
    ret = api.create_loan(asset, amount)
    print(ret)
    time.sleep(20)
    ret = api.repay_loan(asset, amount)
    print(ret)


def loan_and_buy():
    asset = 'USDT'
    amount = 40
    ret = api.create_loan(asset, amount)
    print(ret)

    ret = api.create_buy_order(symbol, quantity=0.003)
    print(ret)


def close_buy():
    asset = 'USDT'
    amount = 40

    ret = api.create_sell_order(symbol, quantity=0.003)
    print(ret)

    ret = api.repay_all(asset)
    print(ret)


def margin_account_info():
    print(api.margin_account_info())


def test_bulk_candle():
    print(api.bulk_klines(symbol, '1h', since='2020-01-31'))


def test_get_klines():
    print(api.get_klines(symbol, '1h', since='2019-01-01', limit=10))


def test_ws_kline():
    api.start_websocket(symbol, '1h', lambda s: print(s))


def get_my_trade():
    print(api.get_my_trades(symbol))

get_my_trade()

