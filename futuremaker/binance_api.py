from binance.client import Client
from binance.enums import *


class BinanceAPI:

    def __init__(self, api_key=None, api_secret=None):
        self.client = Client(api_key, api_secret)

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        # timeframe: Client.KLINE_INTERVAL_1MINUTE
        # since: "1 Jan, 2017"
        klines = self.client.get_historical_klines(symbol, timeframe, since)

        # todo []에 ohlcv 5개 아이템이 차례대로 들어있다.
        result = klines
        return result

    def account_info(self):
        info = self.client.get_margin_account()
        return info

    def create_order(self, symbol, side, price, quantity):
        # order = self.client.create_margin_order(
        #     symbol=symbol,
        #     side=side,
        #     type=ORDER_TYPE_LIMIT,
        #     timeInForce=TIME_IN_FORCE_GTC,
        #     quantity=quantity,
        #     price=price)
        # return order

        #order_market_sell, order_limit_buy, order_limit_sell
        order = self.client.order_market_buy(
            symbol=symbol,
            quantity=quantity)

        return order

    def create_loan(self, asset, amount):
        transaction = self.client.create_margin_loan(asset=asset, amount=amount)
        return transaction

    def repay_loan(self, asset, amount):
        transaction = self.client.repay_margin_loan(asset=asset, amount=amount)
        return transaction

    def asset_detail(self):
        details = self.client.get_asset_details()
        return details
