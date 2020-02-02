import asyncio
import sys

from bots.week_breakout_indicator import WeekIndicator
from futuremaker import utils
from futuremaker.binance_api import BinanceAPI
from futuremaker.bot import Bot
from futuremaker.algo import Algo
from futuremaker.position_type import Type, Yoil


class WeekBreakout(Algo):
    def __init__(self, base='BTC', quote='USDT', floor_decimals=3, init_capital=10000, max_budget=10000,
                 week_start=Yoil.MON, hour_start=0, long_rate=0.5, short_rate=0.5):
        super().__init__(base=base, quote=quote, floor_decimals=floor_decimals, init_capital=init_capital,
                         max_budget=max_budget)
        self.weekIndicator = WeekIndicator(week_start, hour_start, long_rate, short_rate)

    def ready(self):
        self.wallet_summary()

    # 1. 손절하도록. 손절하면 1일후에 집입토록.
    # 2. MDD 측정. 손익비 측정.
    # 3. 자본의 %를 투입.
    def update_candle(self, df, candle):
        this_time = candle.name
        candle = self.weekIndicator.update(df, candle)

        self.estimated_profit(this_time, candle.close)

        # 1. candle 이 long_break 를 뚫으면 롱 포지션을 취한다.
        if candle.open < candle.long_break < candle.close:
            # 하루이상 지나야 매매한다.
            if (this_time - self.position_entry_time).days >= 1:
                if self.position_quantity < 0:
                    # 먼저 숏 포지션을 CLOSE 한다.
                    quantity = self.close_short()
                    self.calc_close(this_time, candle.close, self.position_entry_price, -quantity)
                # 롱 진입
                if self.position_quantity == 0:
                    self.open_long()
                    self.calc_open(Type.LONG, this_time, candle.close, candle.long_break)

        # 2. candle 이 short_break 를 뚫으면 숏 포지션을 취한다.
        if candle.close < candle.short_break < candle.open:
            if (this_time - self.position_entry_time).days >= 1:
                # short 수행.
                if self.position_quantity > 0:
                    quantity = self.close_long()
                    self.calc_close(this_time, candle.close, self.position_entry_price, quantity)
                    # 먼저 롱 포지션을 CLOSE 한다.
                # 숏 진입
                if self.position_quantity == 0:
                    self.open_short()
                    self.calc_open(Type.SHORT, this_time, candle.close, candle.short_break)

        # 3. 롱 포지션 손절.
        if self.position_quantity > 0:
            if candle.close < min(candle.long_break,
                                  self.position_losscut_price) < candle.open:  # 롱 라인을 뚫고 내려올때. min을 사용하여 좀더 여유확보.
                if (this_time - self.position_entry_time).days >= 1:
                    quantity = self.close_long()
                    self.calc_close(this_time, candle.close, self.position_entry_price, quantity)

        # 4. 숏 포지션 손절.
        if self.position_quantity < 0:
            if candle.close > min(candle.short_break,
                                  self.position_losscut_price) > candle.open:  # 숏 라인을 뚫고 올라올때. min을 사용하여 빠른 손절.
                if (this_time - self.position_entry_time).days >= 1:
                    quantity = self.close_short()
                    self.calc_close(this_time, candle.close, self.position_entry_price, -quantity)


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    year = 2018
    test_bot = Bot(None, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
                   candle_period='1h',
                   test_start=f'{year}-01-01', test_end=f'{year}-12-31',
                   test_data='../candle_data/BINANCE_BTCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_BTCUSD, 120.csv'
                   # test_data='../candle_data/BINANCE_ETCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_ETHUSD, 60.csv'
                   )
    real_bot = Bot(BinanceAPI(), symbol='BTCUSDT', candle_limit=24 * 7 * 2,
                   backtest=False,
                   candle_period='1m',
                   telegram_bot_token='852670167:AAExawLUJfb-lGKVHQkT5mthCTEOT_BaQrg',
                   telegram_chat_id='352354994'
                   )

    algo = WeekBreakout(base='BTC', quote='USDT', floor_decimals=3, init_capital=10000, max_budget=1000000,
                        week_start=Yoil.MON, hour_start=0, long_rate=0.4, short_rate=0.4)

    # asyncio.run(test_bot.run(algo))
    asyncio.run(real_bot.run(algo))
