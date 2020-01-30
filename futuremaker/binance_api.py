from binance.client import Client
from binance.enums import *


class BinanceAPI:

    def __init__(self, api_key=None, api_secret=None):
        self.client = Client(api_key, api_secret)

    def fetch_ohlcv(self, symbol, timeframe, since=None):
        # since: "1 Jan, 2017"
        if timeframe == '1m':
            interval = Client.KLINE_INTERVAL_1MINUTE
        elif timeframe == '1h':
            interval = Client.KLINE_INTERVAL_1HOUR
        elif timeframe == '1d':
            interval = Client.KLINE_INTERVAL_1DAY

        klines = self.client.get_historical_klines(symbol, interval, start_str=since)
        return klines

    def account_info(self):
        info = self.client.get_margin_account()
        return info

    def create_buy_order(self, symbol, quantity, price=None):
        if price is not None:
            order = self.client.create_margin_order(
                symbol=symbol,
                quantity=quantity,
                price=price,
                side=SIDE_BUY,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC)
        else:
            order = self.client.create_margin_order(
                symbol=symbol,
                quantity=quantity,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET)
        return order

    def create_sell_order(self, symbol, quantity, price=None):
        if price is not None:
            order = self.client.create_margin_order(
                symbol=symbol,
                quantity=quantity,
                price=price,
                side=SIDE_SELL,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC)
        else:
            order = self.client.create_margin_order(
                symbol=symbol,
                quantity=quantity,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET)
        return order

    def create_loan(self, asset, amount):
        transaction = self.client.create_margin_loan(asset=asset, amount=amount)
        return transaction

    def repay_loan(self, asset, amount):
        transaction = self.client.repay_margin_loan(asset=asset, amount=amount)
        return transaction

    def repay_all(self, asset):
        info = self.account_info()
        obj = next(item for item in info['userAssets'] if item['asset'] == asset)
        free = obj['free']
        return self.repay_loan(asset, free)

    def asset_detail(self):
        details = self.client.get_asset_details()
        return details

    def get_tickers(self, symbol):
        tickers = self.client.get_all_tickers()
        return next(item for item in tickers if item['symbol'] == symbol)

    def get_orderbook_tickers(self, symbol):
        """
        :return: {'symbol': 'BTCUSDT', 'bidPrice': '9379.95000000', 'bidQty': '0.26652500', 'askPrice': '9380.00000000',
                    'askQty': '0.22441700'}
        """
        tickers = self.client.get_orderbook_tickers()
        return next(item for item in tickers if item['symbol'] == symbol)