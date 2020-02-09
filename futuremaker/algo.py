import asyncio
import json
import os
import sys
import time
import traceback
from datetime import datetime
from json import JSONDecodeError

import pytz

from futuremaker import utils
from futuremaker.binance_api import BinanceAPI
from futuremaker import log
from futuremaker.position_type import Type


class Algo(object):
    def __init__(self, base, quote, floor_decimals,
                 init_capital, commission_rate,
                 #  트레이딩 최대예산. 이 수치를 넘어서 사지 않는다. 단위는 quote기준.
                 max_budget,
                 paper,
                 buy_unit,  # 나누어 살때 얼마큼씩 살지.
                 buy_delay,  # 나누어 살때 얼마나 쉴지.
                 ):
        self.local_tz = pytz.utc  # 나중에 bot으로부터 다시 설정된다.
        self.backtest = True  # 시작전 Bot으로부터 설정된다.
        self.paper = paper  # 페이퍼 트레이딩 모드로 실제 주문하지 않는다.
        self.api: BinanceAPI = None
        self.base = base
        self.quote = quote
        self.symbol = f'{base}{quote}'
        self.floor_decimals = floor_decimals
        self.commission_rate = commission_rate

        self.init_capital = init_capital
        self.max_budget = max_budget

        self.position_quantity = 0
        self.position_entry_price = 0
        self.position_losscut_price = 0
        # local time 으로 유지된다.
        self.position_entry_time = utils.localtime(datetime.utcfromtimestamp(0) if self.backtest else datetime.utcnow(), self.local_tz)
        self.total_profit = 0.0
        self.total_equity = self.init_capital
        self.win_profit = 0
        self.loss_profit = 0
        self.total_trade = 0
        self.win_trade = 0
        self.lose_trade = 0
        self.max_equity = 0
        self.dd = 0
        self.mdd = 0

        self.loanDelay = 5
        self.buy_unit = buy_unit
        self.buy_delay = buy_delay

        self.STATUS_FILE = f'status-{self.get_name()}.json'
        self.TRADE_FILE = f'trade-{self.get_name()}.json'
        self.DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

    def ready(self):
        """
        봇 시작전 정보를 로드할때 사용.
        """
        pass

    def get_name(self):
        return type(self).__name__

    def load_status(self):
        """
        봇이 시작할때 기존 포지션 정보가 없으므로, 로드하도록 한다.
        """
        if self.backtest:
            return

        # 파일이 없으면 먼저 하나를 만들어준다.
        if not os.path.isfile(self.STATUS_FILE):
            self.save_status()

        with open(self.STATUS_FILE, 'r') as json_file:
            status_data = json.load(json_file)
            self.base = status_data['base']
            self.quote = status_data['quote']
            self.init_capital = status_data['init_capital']
            self.position_quantity = status_data['position_quantity']
            self.position_entry_price = status_data['position_entry_price']
            self.position_losscut_price = status_data['position_losscut_price']
            self.position_entry_time = datetime.strptime(status_data['position_entry_time'], self.DATETIME_FORMAT).replace(tzinfo=self.local_tz)
            # 성능 계산에 필요한 누적수치들..
            self.total_equity = status_data['total_equity']
            self.total_profit = status_data['total_profit']
            self.init_capital = status_data['init_capital']
            self.max_equity = status_data['max_equity']
            self.mdd = status_data['mdd']
            self.total_trade = status_data['total_trade']
            self.win_trade = status_data['win_trade']
            self.win_profit = status_data['win_profit']
            self.lose_trade = status_data['lose_trade']
            self.loss_profit = status_data['loss_profit']

            message = f'==== Load Status ====\n' \
                      f'base[{self.base}] quote[{self.quote}]\n' \
                      f'init_capital[{self.init_capital}]\n' \
                      f'position_quantity[{self.position_quantity}]\n' \
                      f'position_entry_price[{self.position_entry_price}]\n' \
                      f'position_losscut_price[{self.position_losscut_price}]\n' \
                      f'position_entry_time[{self.position_entry_time}]\n' \
                      f'total_equity[{self.total_equity}]\n' \
                      f'total_profit[{self.total_profit}]\n' \
                      f'init_capital[{self.init_capital}]\n' \
                      f'max_equity[{self.max_equity}]\n' \
                      f'mdd[{self.mdd}]\n' \
                      f'total_trade[{self.total_trade}]\n' \
                      f'win_trade[{self.win_trade}]\n' \
                      f'win_profit[{self.win_profit}]\n' \
                      f'lose_trade[{self.lose_trade}]\n' \
                      f'loss_profit[{self.loss_profit}]'

            log.logger.info(message)
            self.send_message(message)

    def save_status(self):
        """
        "base": "BTC",
        "quote": "USDT",
        "init_capital": 10000,
        "position_quantity": -1.34,
        "position_entry_price": 8990.0,
        "position_losscut_price": 8430,
        "position_entry_time": "2020-01-20T00:00:00Z"
        """
        if self.backtest:
            return

        status_data = {
            "base": self.base,
            "quote": self.quote,
            "init_capital": self.init_capital,
            "position_quantity": self.position_quantity,
            "position_entry_price": self.position_entry_price,
            "position_losscut_price": self.position_losscut_price,
            "position_entry_time": datetime.strftime(self.position_entry_time, self.DATETIME_FORMAT),
            # 아래는 트레이딩 성능 계산시 필요한 누적 수치들이다.
            "total_equity": self.total_equity,
            "total_profit": self.total_profit,
            "init_capital": self.init_capital,
            "max_equity": self.max_equity,
            "mdd": self.mdd,
            "total_trade": self.total_trade,
            "win_trade": self.win_trade,
            "win_profit": self.win_profit,
            "lose_trade": self.lose_trade,
            "loss_profit": self.loss_profit,
        }
        with open(self.STATUS_FILE, 'w') as json_file:
            json.dump(status_data, json_file, indent=4)

    def append_trade(self, trade):
        """
        :param trade: 트레이드 객체.
        {
            "tradeTime": "<timestamp10>"
            "datetime": "2020-01-12T00:00:00"
            "symbol" : "BTC/USDT"
            "action" : "SELL",
            "position" : "NONE",
            "price" : 8751.1,
            "quantity": 1.34,python
            "pnl": {
                "total_equity" : 10203,
                "total_profit" : 203,
                "init_capital" : 10000,
                "drawdown" : 10,
                "mdd" : 13.2,
                "total_trade":
            }
        }
        """
        if self.backtest:
            return

        trade_data = []
        if os.path.isfile(self.TRADE_FILE):
            try:
                with open(self.TRADE_FILE, 'r') as file:
                    trade_data = json.load(file)
            except JSONDecodeError:
                pass

        with open(self.TRADE_FILE, 'w') as file:
            trade_data.append(trade)
            json_val = json.dumps(trade_data, indent=4)
            file.write(f'{json_val}\n')

    def _update_candle(self, df, candle):
        try:
            self.estimated_profit(candle.name, candle.close)
            localtime = utils.localtime(candle.name, self.local_tz)
            self.update_candle(df, candle, localtime)
        except Exception as e:
            try:
                exc_info = sys.exc_info()
            finally:
                self.send_message(e)
                traceback.print_exception(*exc_info)
                del exc_info

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

    def close_long(self):
        if self.position_quantity > 0:
            self.position_losscut_price = 0

            if self.backtest or self.paper:
                quantity = self.position_quantity
                self.position_quantity = 0
                return quantity

            # 홀드하던 BTC를 판다.
            quantity = self.position_quantity
            self.safe_sell_order(self.symbol, self.position_quantity)
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
            self.position_losscut_price = 0

            if self.backtest or self.paper:
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
            self.safe_buy_order(self.symbol, quantity)
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

        i = 1
        while True:
            try:
                log.order.info(f'LOAN try {i}.. {asset} {amount}')
                txId = self.api.create_loan(asset, amount)
                log.order.info(f'LOAN txId {txId}')
                time.sleep(self.loanDelay)
                ret, detail = self.api.get_loan(asset, txId)
                log.order.info(f'LOAN ret {ret}')
                if ret == 0:
                    break
            except Exception as e:
                log.logger.error(e)
                log.logger.info(f'차용에 문제가 생겨 {self.loanDelay * 3} 초후에 다시 한번 시도 합니다.')
                time.sleep(self.loanDelay * 3)
                i += 1

        log.order.info(f'LOAN! {asset} {amount}')
        self.send_message(f'Loan! {asset} {amount}')

    def open_long(self):
        if self.backtest or self.paper:
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
        # buy_unit 를 초과할경우 여러번 나누어 사는 것 고려..
        self.safe_buy_order(self.symbol, quantity)

        message = f'Long! {self.symbol} {self.position_quantity}'
        self.send_message(message)
        self.wallet_summary()

    def open_short(self):
        if self.backtest or self.paper:
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

        self.safe_sell_order(self.symbol, quantity)

        message = f'Short! {self.symbol} {self.position_quantity}'
        self.send_message(message)
        self.wallet_summary()

    def safe_buy_order(self, symbol, quantity):
        togo = quantity
        while togo > 0:
            tobuy = min(self.buy_unit, togo)
            ret = self.api.create_buy_order(symbol, tobuy)
            togo -= tobuy
            self.position_quantity += tobuy
            message = f'BUY > {ret["status"]} {ret["executedQty"]} {self.position_quantity}/{quantity}'
            log.order.info(message)
            self.send_message(message)
            if togo > 0:
                time.sleep(self.buy_delay)

    def safe_sell_order(self, symbol, quantity):
        togo = quantity
        while togo > 0:
            tobuy = min(self.buy_unit, togo)
            ret = self.api.create_sell_order(symbol, tobuy)
            togo -= tobuy
            self.position_quantity -= tobuy
            message = f'SELL > {ret["status"]} {ret["executedQty"]} {-self.position_quantity}/{quantity}'
            log.order.info(message)
            self.send_message(message)
            if togo > 0:
                time.sleep(self.buy_delay)

    def wallet_summary(self):
        if self.backtest or self.paper:
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

    def calc_open(self, type, localtime, price, losscut_price):
        if self.backtest or self.paper:
            # 백테스트는 open_short, open_long을 실행하지 않으므로, self.position_quantity 룰 여기서 계산해준다.
            total_value = utils.floor(self.total_equity / price, self.floor_decimals)
            max_amount = utils.floor(self.max_budget / price, self.floor_decimals)
            quantity = min(max_amount, total_value)
            self.position_quantity = -quantity if type == Type.SHORT else quantity

        message = f'{localtime} OPEN {type} {self.symbol} {self.position_quantity}@{price}\n' \
                  f'============================'
        log.position.info(message)
        self.send_message(message)

        self.position_entry_price = price
        self.position_losscut_price = losscut_price
        self.position_entry_time = localtime
        # 상태저장
        self.save_status()
        self.append_trade({
            "tradeTime": localtime.timestamp(),
            "datetime": localtime.strftime(self.DATETIME_FORMAT),
            "symbol": self.symbol,
            "position": type,
            "price": price,
            "quantity": self.position_quantity,
        })

    def calc_close(self, localtime, exit_price, entry_price, quantity):
        # 이익 확인.
        profit = quantity * ((exit_price - entry_price) / entry_price) * exit_price
        commission = self.commission_rate / 100 * 2 * abs(profit)  # 사고 파는 수수료라 2를 곱한다.
        profit -= commission
        profit_pct = abs(profit / quantity / entry_price * 100)
        profit_pct = profit_pct if profit > 0 else -profit_pct
        message = f'{localtime} CLOSE {quantity}@{exit_price} PROFIT: {profit:.0f} ({profit_pct:0.2f}%)'
        log.position.info(message)
        self.send_message(message)

        self.total_profit += profit
        total_profit_pct = self.total_profit / self.init_capital * 100.0
        self.total_equity = self.init_capital + self.total_profit
        self.max_equity = max(self.max_equity, self.total_equity)
        dd = (self.max_equity - self.total_equity) * 100 / self.max_equity \
            if self.max_equity > 0 and self.max_equity - self.total_equity > 0 else 0
        self.mdd = max(self.mdd, dd)
        # trade 횟수.
        self.total_trade += 1
        if profit > 0:
            self.win_trade += 1
            self.win_profit += profit
        else:
            self.lose_trade += 1
            self.loss_profit += -profit

        win_pct = (self.win_trade / self.total_trade) * 100 if self.total_trade > 0 else 0

        pnl_ratio = 0
        if self.lose_trade > 0 and self.win_trade > 0:
            pnl_ratio = (self.win_profit / self.win_trade) / (self.loss_profit / self.lose_trade)
        else:
            pnl_ratio = 0

        # 초기화
        self.position_quantity = 0
        self.position_entry_time = localtime
        # 상태저장
        self.save_status()
        self.append_trade({
            "tradeTime": localtime.timestamp(),
            "datetime": localtime.strftime(self.DATETIME_FORMAT),
            "symbol": self.symbol,
            "position": 'NONE',
            "entry_price": entry_price,
            "price": exit_price,
            "quantity": quantity,
            "pnl": {
                "profit": profit,
                "profit_pct": profit_pct,
                "total_equity": self.total_equity,
                "total_profit": self.total_profit,
                "total_profit_pct": total_profit_pct,
                "init_capital": self.init_capital,
                "max_equity": self.max_equity,
                "drawdown": dd,
                "mdd": self.mdd,
                "total_trade": self.total_trade,
                "win_trade": self.win_trade,
                "win_profit": self.win_profit,
                "lose_trade": self.lose_trade,
                "loss_profit": self.loss_profit,
                "win_pct": win_pct,
                "pnl_ratio": pnl_ratio,
            }
        })
        # 요약
        summary = f'SUMMARY TOT_EQUITY:{self.total_equity:.0f} ' \
                  f'TOT_PROFIT:{self.total_profit:.0f} ({total_profit_pct:.2f}%) ' \
                  f'DD:{dd:0.1f}% MDD:{self.mdd:0.1f}% ' \
                  f'TOT_TRADE:{self.total_trade} ' \
                  f'WIN%:{win_pct:2.1f}% ' \
                  f'P/L:{pnl_ratio:0.1f}\n' \
                  f'============================'
        log.position.info(summary)
        self.send_message(summary)

    def estimated_profit(self, localtime, current_price):
        if self.position_entry_price == 0:
            return

        est_profit = self.position_quantity * (
                (current_price - self.position_entry_price) / self.position_entry_price) * current_price
        estimated_equity = self.total_equity + est_profit
        max_equity = max(self.max_equity, estimated_equity)
        drawdown = (max_equity - estimated_equity) * 100 / max_equity \
            if max_equity > 0 and max_equity - estimated_equity > 0 else 0
        if drawdown > self.mdd:
            self.mdd = max(self.mdd, drawdown)
            message = f'{localtime} New MDD:{drawdown:0.2f}% @{current_price} TOT_EQUITY:{estimated_equity:0.0f}'
            log.logger.info(message)
            self.send_message(message)
