import asyncio
import sys
from datetime import datetime

from bots.week_breakout_indicator import WeekIndicator
from futuremaker import utils
from futuremaker.binance_api import BinanceAPI
from futuremaker.bot import Bot
from futuremaker.algo import Algo
from futuremaker import log

class Type:
    LONG = 'LONG'
    SHORT = 'SHORT'


class AlertGo(Algo):
    def __init__(self):
        self.init_capital = 10000
        self.default_amount = self.init_capital * 0.8
        self.long_amount = 0
        self.long_entry_price = 0
        self.long_losscut_price = 0
        self.short_amount = 0
        self.short_entry_price = 0
        self.short_losscut_price = 0
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

    # 1. 손절하도록. 손절하면 1일후에 집입토록.
    # 2. MDD 측정. 손익비 측정.
    # 3. 자본의 %를 투입.
    def update_candle(self, df, candle):
        print('strat: ', candle)
        time = candle.name

        # 롤 진입
        if self.short_amount > 0 and self.long_amount == 0:
            self.close_position(time, candle.close, self.short_entry_price, -self.short_amount)
            self.open_position(Type.LONG, time, candle.close, candle.long_break)

        # 숏 진입
        if self.short_amount == 0 and self.long_amount > 0:
            self.close_position(time, candle.close, self.long_entry_price, self.long_amount)
            self.open_position(Type.SHORT, time, candle.close, candle.short_break)

    def show_summary(self):
        summary = f'SUMMARY TOT_EQUITY:{self.total_equity:.0f} TOT_PROFIT:{self.total_profit:.0f} DD:{self.dd:0.1f}% MDD:{self.mdd:0.1f}% TOT_TRADE:{self.total_trade} WIN%:{(self.win_trade / self.total_trade) * 100 if self.total_trade > 0 else 0:2.1f}% P/L:{self.pnl_ratio:0.1f}'
        log.position.info(summary)
        self.send_telegram(summary)

    def open_position(self, type, time, price, losscut_price):
        amount = int(self.total_equity * 1.0)
        log.position.info(f'{time} OPEN {type} {amount}@{price}')
        self.send_telegram(f'{time} OPEN {type} {amount}@{price}')

        if type == Type.SHORT:
            self.short_amount += amount
            self.short_entry_price = price
            self.short_losscut_price = losscut_price
        elif type == Type.LONG:
            self.long_amount += amount
            self.long_entry_price = price
            self.long_losscut_price = losscut_price

        self.position_entry_time = time

    def close_position(self, time, exit_price, entry_price, amount):
        # 이익 확인.
        profit = amount * ((exit_price - entry_price) / entry_price)
        log.position.info(f'{time} CLOSE {amount}@{exit_price} PROFIT: {profit:.0f}')
        self.send_telegram(f'{time} CLOSE {amount}@{exit_price} PROFIT: {profit:.0f}')

        self.total_profit += profit
        self.total_equity = self.init_capital + self.total_profit
        self.max_equity = max(self.max_equity, self.total_equity)
        self.dd = (
                          self.max_equity - self.total_equity) * 100 / self.max_equity if self.max_equity > 0 and self.max_equity - self.total_equity > 0 else 0
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
        self.long_amount = 0
        self.short_amount = 0
        self.position_entry_time = time
        # 요약
        self.show_summary()


class ExchangeAPI:
    def __init__(self):
        self.data = {}

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        # todo []에 ohlcv 5개 아이템이 차례대로 들어있다.
        pass


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])

    # api 에 key와 secret 을 모두 셋팅.
    # api 는 오더도 가능하지만 캔들정보도 확인가능. 1분마다 확인.
    api = None
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
                   # telegram_bot_token='852670167:AAExawLUJfb-lGKVHQkT5mthCTEOT_BaQrg',
                   # telegram_chat_id='352354994'
                   )

    algo = AlertGo()

    # asyncio.run(test_bot.run(algo))
    asyncio.run(real_bot.run(algo))
