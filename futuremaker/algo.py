import asyncio
import time
from datetime import datetime

from futuremaker import utils
from futuremaker.binance_api import BinanceAPI
from futuremaker import log
from futuremaker.position_type import Type


class Algo(object):
    def __init__(self, base, quote, floor_decimals,
                 init_capital,
                 #  트레이딩 최대예산. 이 수치를 넘어서 사지 않는다. 단위는 quote기준.
                 max_budget
                 ):
        self.backtest = True  # 시작전 Bot으로부터 설정된다.
        self.api: BinanceAPI = None
        self.base = base
        self.quote = quote
        self.symbol = f'{base}{quote}'
        self.position_quantity = 0
        self.floor_decimals = floor_decimals

        self.init_capital = init_capital
        self.max_budget = max_budget

        self.position_quantity = 0
        self.position_entry_price = 0
        self.position_losscut_price = 0
        self.position_entry_time = datetime.fromtimestamp(0)

        self.total_profit = 0.0
        self.total_equity = self.init_capital
        self.win_profit = 0
        self.loss_profit = 0
        self.total_trade = 0
        self.win_trade = 0
        self.lose_trade = 0
        self.pnl_ratio = 0
        self.max_equity = 0
        self.dd = 0
        self.mdd = 0

        self.loanDelay = 3
        self.buyDelay = 60
        self.buyBTCUnit = 1

    def get_name(self):
        return type(self).__name__

    def update_candle(self, df, candle):
        """
        캔들이 업데이트되어 dict가 들어온다.
        :param df: pandas.DataFrame
        :param candle: dict
        :return:
        """
        pass

    def send_message(self, text):
        pass

    def show_summary(self):
        summary = f'SUMMARY TOT_EQUITY:{self.total_equity:.0f} ' \
                  f'TOT_PROFIT:{self.total_profit:.0f} ({self.total_profit/self.total_equity*100.0:.2f}%) ' \
                  f'DD:{self.dd:0.1f}% MDD:{self.mdd:0.1f}% ' \
                  f'TOT_TRADE:{self.total_trade} ' \
                  f'WIN%:{(self.win_trade / self.total_trade) * 100 if self.total_trade > 0 else 0:2.1f}% ' \
                  f'P/L:{self.pnl_ratio:0.1f}\n' \
                  f'============================'
        log.position.info(summary)
        self.send_message(summary)

    def close_long(self):
        if self.position_quantity > 0:
            if self.backtest:
                quantity = self.position_quantity
                self.position_quantity = 0
                return quantity

            # 홀드하던 BTC를 판다.
            quantity = self.position_quantity
            ret = self.api.create_sell_order(self.symbol, self.position_quantity)
            log.order.info(f'CLOSE LONG > {ret}')
            amount = self.api.repay_all(self.quote)
            log.order.info(f'REPAY ALL > {amount}')
            message = f'Close Long {self.symbol} {self.position_quantity}\nRepay All {self.base} {amount}'
            self.send_message(message)
            self.position_quantity = 0
            self.wallet_summary()
            return quantity
        else:
            log.order.info(f'CLOSE LONG > No Long Position to close!')

    def close_short(self):

        if self.position_quantity < 0:
            if self.backtest:
                quantity = -self.position_quantity
                self.position_quantity = 0
                return quantity

            # 1. USDT 가 충분한지 확인해서 부족하면 빌린다. 숏 포지션에서 가격이 올랐을 경우가 이에 속한다.
            quantity = -self.position_quantity
            ask_price = self.api.get_price(self.symbol, price_type='askPrice')
            budget = quantity * ask_price
            balance = self.api.get_balance(self.quote)
            if budget > balance:
                loan_amount = budget - balance
                loan_amount = utils.round_up(loan_amount, 10)  # 10의 배수를 얻는다.
                self.make_loan(self.quote, loan_amount)

            # 2. 자금을 가지고 BTC를 산다.
            ret = self.api.create_buy_order(self.symbol, quantity)
            log.order.info(f'CLOSE SHORT > {ret}')
            amount = self.api.repay_all(self.base)
            log.order.info(f'REPAY ALL > {amount}')
            message = f'Close Short {self.symbol} {quantity}\nRepay All {self.base} {amount}'
            self.send_message(message)
            self.position_quantity = 0
            self.wallet_summary()
            return quantity
        else:
            log.order.info(f'CLOSE SHORT > No Short Position to close!')

    def make_loan(self, asset, amount):
        if self.backtest:
            return

        log.order.info(f'LOAN.. {asset} {amount}')
        txId = self.api.create_loan(asset, amount)
        time.sleep(self.loanDelay)
        ret, detail = self.api.get_loan(asset, txId)
        if ret != 0:
            log.order.info(f'LOAN FAIL {detail}')
            return
        log.order.info(f'LOAN! {asset} {amount}')
        self.send_message(f'Loan! {asset} {amount}')

    def open_long(self):
        if self.backtest:
            return

        log.order.info('========= GO LONG ==========')
        # 1. 빌린다.
        # 얼마나 빌릴지 계산.
        price = self.api.get_price(self.symbol)
        info = self.api.margin_account_info()
        total_value = utils.floor_int(price * float(info["totalNetAssetOfBtc"]), 1)
        max_budget = utils.floor_int(self.max_budget, 1)  # BTC 가격에 과적합된 코드
        amount = min(max_budget, total_value)
        self.make_loan(self.quote, amount)

        # 2. 산다.
        quantity = utils.floor(amount / price, self.floor_decimals)
        message = f'Long.. {self.symbol} {quantity}'
        self.send_message(message)
        # 1btc를 초과할경우 여러번 나누어 사는 것 고려..
        togo = quantity
        while togo > 0:
            tobuy = min(self.buyBTCUnit, togo)
            ret = self.api.create_buy_order(self.symbol, tobuy)
            togo -= tobuy
            self.position_quantity += tobuy
            message = f'BUY > {ret["status"]} {ret["executedQty"]} {self.position_quantity}/{quantity}'
            log.order.info(message)
            self.send_message(message)
            if togo > 0:
                time.sleep(self.buyDelay)

        message = f'Long! {self.symbol} {self.position_quantity}'
        self.send_message(message)
        self.wallet_summary()

    def open_short(self):
        if self.backtest:
            return

        log.order.info('========= GO SHORT ==========')
        # 1. base 자산을 빌린다.
        price = self.api.get_price(self.symbol)
        info = self.api.margin_account_info()
        total_value = utils.floor(float(info["totalNetAssetOfBtc"]), self.floor_decimals)
        max_amount = utils.floor(self.max_budget / price, self.floor_decimals)  # BTC 가격에 과적합된 코드
        quantity = min(max_amount, total_value)
        self.make_loan(self.base, quantity)

        # 2. 판다.
        # 1btc를 초과할경우 여러번 나누어 파는 것 고려..
        message = f'Short.. {self.symbol} {quantity}'
        self.send_message(message)

        togo = quantity
        while togo > 0:
            tobuy = min(self.buyBTCUnit, togo)
            ret = self.api.create_sell_order(self.symbol, tobuy)
            togo -= tobuy
            self.position_quantity -= tobuy
            message = f'SELL > {ret["status"]} {ret["executedQty"]} {-self.position_quantity}/{quantity}'
            log.order.info(message)
            self.send_message(message)
            if togo > 0:
                time.sleep(self.buyDelay)

        message = f'Short! {self.symbol} {self.position_quantity}'
        self.send_message(message)
        self.wallet_summary()

    def wallet_summary(self):
        if self.backtest:
            return

        time.sleep(1)
        price = self.api.get_price('BTCUSDT')
        info = self.api.margin_account_info()
        desc = f'{datetime.now()}'
        desc = f'{desc}\n자산가치[$ {utils.floor_int(price * float(info["totalNetAssetOfBtc"]), 0)} = ' \
               f'{utils.floor(float(info["totalNetAssetOfBtc"]), 3)} BTC]' \
               f'\n마진레벨[{utils.floor(float(info["marginLevel"]), 2)}]\n'

        for item in info['userAssets']:
            if float(item['netAsset']) != 0.0 or float(item['free']) != 0.0:
                desc = f"{desc}{item['asset']}: " \
                       f"가능[{utils.floor(float(item['free']), 3)}] " \
                       f"차용[{0 if float(item['borrowed']) == 0.0 else utils.floor(float(item['borrowed']), 3)}] " \
                       f"순자산[{utils.floor(float(item['netAsset']), 3)}]\n"
        self.send_message(desc)
        log.logger.info(desc)

    def calc_open(self, type, time, price, losscut_price):
        if self.backtest:
            # 백테스트는 open_short, open_long을 실행하지 않으므로, self.position_quantity 룰 여기서 계산해준다.
            total_value = utils.floor(self.total_equity / price, self.floor_decimals)
            max_amount = utils.floor(self.max_budget / price, self.floor_decimals)
            quantity = min(max_amount, total_value)
            self.position_quantity = -quantity if type == Type.SHORT else quantity

        message = f'OPEN {type} {self.symbol} {self.position_quantity}@{price}\n' \
                  f'============================'
        log.position.info(message)
        self.send_message(message)

        self.position_entry_price = price
        self.position_losscut_price = losscut_price
        self.position_entry_time = time

    def calc_close(self, time, exit_price, entry_price, quantity):
        # 이익 확인.
        profit = quantity * ((exit_price - entry_price) / entry_price)
        message = f'CLOSE {quantity}@{exit_price} PROFIT: {profit:.0f}'
        log.position.info(message)
        self.send_message(message)

        self.total_profit += profit
        self.total_equity = self.init_capital + self.total_profit
        self.max_equity = max(self.max_equity, self.total_equity)
        self.dd = (self.max_equity - self.total_equity) * 100 / self.max_equity \
            if self.max_equity > 0 and self.max_equity - self.total_equity > 0 else 0
        self.mdd = max(self.mdd, self.dd)
        # trade 횟수.
        self.total_trade += 1
        if profit > 0:
            self.win_trade += 1
            self.win_profit += profit
        else:
            self.lose_trade += 1
            self.loss_profit += -profit
        if self.lose_trade > 0 and self.win_trade > 0:
            self.pnl_ratio = (self.win_profit / self.win_trade) / (self.loss_profit / self.lose_trade)
        else:
            self.pnl_ratio = 0

        # 초기화
        self.position_quantity = 0
        self.position_entry_time = time
        # 요약
        self.show_summary()