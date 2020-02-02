import asyncio
import signal
import sys
import time
import traceback
from datetime import datetime

import math

from futuremaker import utils
from futuremaker.binance_api import BinanceAPI
from futuremaker.bot import Bot
from futuremaker.algo import Algo
from futuremaker import log
from futuremaker.position_type import Type


class AlertGo(Algo):
    def __init__(self, base='BTC', quote='USDT', floor_decimals=3):
        self.api: BinanceAPI = None
        self.base = base
        self.quote = quote
        self.symbol = f'{base}{quote}'
        self.position_quantity = 0
        self.floor_decimals = floor_decimals

        self.init_capital = 10000
        #  트레이딩 최대예산. 이 수치를 넘어서 사지 않는다. 단위는 quote기준.
        self.max_budget = 50

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

    def ready(self):
        self.wallet_summary()

    # 1. 손절하도록. 손절하면 1일후에 집입토록.
    # 2. MDD 측정. 손익비 측정.
    # 3. 자본의 %를 투입.
    def update_candle(self, df, candle):
        try:
            time = candle.name

            # 첫진입.
            if self.position_quantity == 0:
                self.open_short()
                self.calc_open(Type.SHORT, time, candle.close, 0)
            else:
                # 롱 진입
                if self.position_quantity < 0:
                    log.logger.info('-- Enter Long')
                    quantity = self.close_short()
                    self.calc_close(time, candle.close, self.position_entry_price, quantity)
                    self.open_long()
                    self.calc_open(Type.LONG, time, candle.close, 0)

                # 숏 진입
                elif self.position_quantity > 0:
                    log.logger.info('-- Enter Short')
                    quantity = self.close_long()
                    self.calc_close(time, candle.close, self.position_entry_price, quantity)
                    self.open_short()
                    self.calc_open(Type.SHORT, time, candle.close, 0)
        except Exception as e:
            try:
                exc_info = sys.exc_info()
            finally:
                self.send_message(e)
                traceback.print_exception(*exc_info)
                del exc_info

    def show_summary(self):
        summary = f'SUMMARY TOT_EQUITY:{self.total_equity:.0f} ' \
                  f'TOT_PROFIT:{self.total_profit:.0f} ' \
                  f'DD:{self.dd:0.1f}% MDD:{self.mdd:0.1f}% ' \
                  f'TOT_TRADE:{self.total_trade} ' \
                  f'WIN%:{(self.win_trade / self.total_trade) * 100 if self.total_trade > 0 else 0:2.1f}% ' \
                  f'P/L:{self.pnl_ratio:0.1f}'
        log.position.info(summary)
        self.send_message(summary)

    def close_long(self):
        if self.position_quantity > 0:
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
            quantity = -self.position_quantity
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

    def open_long(self):
        log.order.info('========= GO LONG ==========')
        # 1. 빌린다.
        # 얼마나 빌릴지 계산.
        price = self.api.get_price(self.symbol)
        info = self.api.margin_account_info()
        total_value = utils.floor_int(price * float(info["totalNetAssetOfBtc"]), 1)
        max_budget = utils.floor_int(self.max_budget, 1)  # BTC 가격에 과적합된 코드
        amount = min(max_budget, total_value)
        log.order.info(f'LOAN.. {self.quote} {amount}')
        txId = self.api.create_loan(self.quote, amount)
        time.sleep(self.loanDelay)
        ret, detail = self.api.get_loan(self.quote, txId)
        if ret != 0:
            log.order.info(f'LOAN FAIL {detail}')
            return
        self.send_message(f'Loan! {self.quote} {amount}')

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
        log.order.info('========= GO SHORT ==========')
        # 1. base 자산을 빌린다.
        price = self.api.get_price(self.symbol)
        info = self.api.margin_account_info()
        total_value = utils.floor(float(info["totalNetAssetOfBtc"]), self.floor_decimals)
        max_budget = utils.floor(self.max_budget / price, self.floor_decimals)  # BTC 가격에 과적합된 코드
        quantity = min(max_budget, total_value)
        log.order.info(f'LOAN.. {self.base} {quantity}')
        txId = self.api.create_loan(self.base, quantity)
        time.sleep(self.loanDelay)
        ret, detail = self.api.get_loan(self.base, txId)
        if ret != 0:
            log.order.info(f'LOAN FAIL {detail}')
            return
        self.send_message(f'Loan! {self.base} {quantity}')

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
        price = self.api.get_price('BTCUSDT')
        info = self.api.margin_account_info()
        desc = f'{datetime.now()}'
        desc = f'{desc}\n자산가치[$ {utils.floor_int(price * float(info["totalNetAssetOfBtc"]), 0)} = ' \
               f'{utils.floor(float(info["totalNetAssetOfBtc"]), 3)} BTC]' \
               f'\n마진레벨[{utils.floor(float(info["marginLevel"]), 2)}]\n'

        for item in info['userAssets']:
            if float(item['netAsset']) != 0.0 or float(item['free']) != 0.0:
                desc = f"{desc}{item['asset']}: " \
                       f"가능[{item['free']}] " \
                       f"차용[{0 if float(item['borrowed']) == 0.0 else item['borrowed']}] " \
                       f"순자산[{item['netAsset']}]\n"
        self.send_message(desc)
        log.logger.info(desc)

    def calc_open(self, type, time, price, losscut_price):
        message = f'OPEN {type} {self.symbol} {self.position_quantity}@{price}'
        log.position.info(message)
        self.send_message(message)

        self.position_entry_price = price
        self.position_losscut_price = losscut_price
        self.position_entry_time = time

    def calc_close(self, time, exit_price, entry_price, quantity):
        # 이익 확인.
        profit = quantity * ((exit_price - entry_price) / entry_price)
        log.position.info(f'CLOSE {quantity}@{exit_price} PROFIT: {profit:.0f}')
        self.send_message(f'CLOSE {quantity}@{exit_price} PROFIT: {profit:.0f}')

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

    def close_all(self, signum, frame):
        """Log to system log. Do not spend too much time after receipt of TERM."""
        print('Exit! ', signum)
        # syslog.syslog(syslog.LOG_CRIT, 'Signal Number:%d {%s}' % (signum, frame))
        # sys.exit(0)


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])

    # api 에 key와 secret 을 모두 셋팅.
    # api 는 오더도 가능하지만 캔들정보도 확인가능. 1분마다 확인.
    alert = None
    api = BinanceAPI()

    year = 2019
    test_bot = Bot(api, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
                   candle_period='1h',
                   test_start=f'{year}-01-01', test_end=f'{year}-12-31',
                   test_data='../candle_data/BINANCE_BTCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_BTCUSD, 120.csv'
                   # test_data='../candle_data/BINANCE_ETCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_ETHUSD, 60.csv'
                   )
    real_bot = Bot(api, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
                   backtest=False, dry_run=False,
                   candle_period='1m',
                   telegram_bot_token='852670167:AAExawLUJfb-lGKVHQkT5mthCTEOT_BaQrg',
                   telegram_chat_id='352354994'
                   )

    algo = AlertGo(base='BTC', quote='USDT', floor_decimals=3)

    # register handler for SIGTERM(15) signal
    signal.signal(signal.SIGTERM, algo.close_all)

    # algo.api = api
    # algo.wallet_summary()
    # asyncio.run(test_bot.run(algo))
    asyncio.run(real_bot.run(algo))



