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
    def test(s):
        time.sleep(5)
        import datetime
        print(datetime.datetime.fromtimestamp(s['E']/1000))
        # callback은 처리되지 않으면 밀린다. 즉, update_candle에서 시간이 몇시간 걸린다면, 그다음 들어오는 candle은 한참 이전의 캔들이 들어옴.
    api.start_websocket(symbol, '1m', test)


def get_my_trade():
    print(api.get_my_trades(symbol))


def test_get_balance():
    print(api.get_balance('USDT'))


test_ws_kline()
