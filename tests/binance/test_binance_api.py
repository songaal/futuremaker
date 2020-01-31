import time
import os
from futuremaker.binance_api import BinanceAPI

symbol = 'BTCUSDT'
key = os.getenv('key')
secret = os.getenv('secret')
api = BinanceAPI(key, secret)


def loan_test():
    # asset = 'USDT'
    asset = 'BTC'
    amount = 0.003
    ret = api.create_loan(asset, amount)
    print(ret)
    time.sleep(20)
    ret = api.repay_loan(asset, amount)
    print(ret)


def loan_buy_and_close():
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


def get_tickers():
    s = api.get_tickers(symbol)
    print(s)
    price = s['price']
    print(f'price: {price}')


def get_orderbook_tickers():
    s = api.get_orderbook_tickers(symbol)
    print(s)
    # price = s['price']
    # print(f'price: {price}')


def get_account():
    print(api.account_info())


def test_bulk_candle():
    print(api.bulk_klines(symbol, '1h', since='2020-01-31'))


def test_get_klines():
    print(api.get_klines(symbol, '1h', since='2019-01-01', limit=10))


def test_ws_kline():
    api.start_websocket(symbol, '1h', lambda s: print(s))


test_ws_kline()

