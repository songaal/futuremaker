import asyncio
import sys
from datetime import datetime

from bots.week_breakout_indicator import WeekIndicator
from futuremaker import utils
from futuremaker.bot import Bot
from futuremaker.algo import Algo
from futuremaker import log


class Yoil:
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6


class Type:
    LONG = 'LONG'
    SHORT = 'SHORT'


class AlertGo(Algo):
    """
    # TODO 봇이 재시작하면 상태 변수들이 사라지는데 어떻게 저장해놓을 것인가... long_amount, long_losscut_price, pnl_ratio ... 또한 시작일자에 따라서
      통계수치는 다를수 있다..
      히스토리를 위해서는 디비가 필수일듯하다.sqlite를 쓰자.
    """
    def __init__(self, week_start=Yoil.MON, hour_start=0, long_rate=0.5, short_rate=0.5):
        self.pyramiding = 1
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
        self.weekIndicator = WeekIndicator(week_start, hour_start, long_rate, short_rate)

    # 1. 손절하도록. 손절하면 1일후에 집입토록.
    # 2. MDD 측정. 손익비 측정.
    # 3. 자본의 %를 투입.
    async def update_candle(self, df, candle):
        time = candle.name
        candle = self.weekIndicator.update(df, candle)

        # 1. candle 이 long_break 를 뚫으면 롱 포지션을 취한다.
        if candle.open < candle.long_break < candle.close:
            # 하루이상 지나야 매매한다.
            if (time - self.position_entry_time).days >= 1:
                if self.long_amount == 0:
                    # 먼저 숏 포지션을 CLOSE 한다.
                    if self.short_amount > 0:
                        await self.close_position(time, candle.close, self.short_entry_price, -self.short_amount)
                # 롱 진입
                if self.short_amount == 0 and self.long_amount == 0:
                    await self.open_position(Type.LONG, time, candle.close, candle.long_break)

        # 2. candle 이 short_break 를 뚫으면 숏 포지션을 취한다.
        if candle.close < candle.short_break < candle.open:
            if (time - self.position_entry_time).days >= 1:
                # short 수행.
                if self.short_amount == 0:
                    # 먼저 롱 포지션을 CLOSE 한다.
                    if self.long_amount > 0:
                        await self.close_position(time, candle.close, self.long_entry_price, self.long_amount)
                # 숏 진입
                if self.short_amount == 0 and self.long_amount == 0:
                    await self.open_position(Type.SHORT, time, candle.close, candle.short_break)

        # 3. 롱 포지션 손절.
        if self.long_amount > 0:
            if candle.close < min(candle.long_break, self.long_losscut_price) < candle.open:  # 롱 라인을 뚫고 내려올때. min을 사용하여 좀더 여유확보.
                if (time - self.position_entry_time).days >= 1:
                    await self.close_position(time, candle.close, self.long_entry_price, self.long_amount)

        # 4. 숏 포지션 손절.
        if self.short_amount > 0:
            if candle.close > min(candle.short_break, self.short_losscut_price) > candle.open:  # 숏 라인을 뚫고 올라올때. min을 사용하여 빠른 손절.
                if (time - self.position_entry_time).days >= 1:
                    await self.close_position(time, candle.close, self.short_entry_price, -self.short_amount)

    async def show_summary(self):
        summary = f'SUMMARY TOT_EQUITY:{self.total_equity:.0f} TOT_PROFIT:{self.total_profit:.0f} DD:{self.dd:0.1f}% MDD:{self.mdd:0.1f}% TOT_TRADE:{self.total_trade} WIN%:{(self.win_trade / self.total_trade) * 100 if self.total_trade > 0 else 0:2.1f}% P/L:{self.pnl_ratio:0.1f}'
        log.position.info(summary)
        await self.send_telegram(summary)

    async def open_position(self, type, time, price, losscut_price):
        amount = int(self.total_equity * 1.0)
        log.position.info(f'{time} OPEN {type} {amount}@{price}')
        await self.send_telegram(f'{time} OPEN {type} {amount}@{price}')

        if type == Type.SHORT:
            self.short_amount += amount
            self.short_entry_price = price
            self.short_losscut_price = losscut_price
        elif type == Type.LONG:
            self.long_amount += amount
            self.long_entry_price = price
            self.long_losscut_price = losscut_price

        self.position_entry_time = time

    async def close_position(self, time, exit_price, entry_price, amount):
        # 이익 확인.
        profit = amount * ((exit_price - entry_price) / entry_price)
        log.position.info(f'{time} CLOSE {amount}@{exit_price} PROFIT: {profit:.0f}')
        await self.send_telegram(f'{time} CLOSE {amount}@{exit_price} PROFIT: {profit:.0f}')

        self.total_profit += profit
        self.total_equity = self.init_capital + self.total_profit
        self.max_equity = max(self.max_equity, self.total_equity)
        self.dd = (self.max_equity - self.total_equity) * 100 / self.max_equity if self.max_equity > 0 and self.max_equity - self.total_equity > 0 else 0
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
        await self.show_summary()


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
    api = ExchangeAPI()

    # 2018 TOT_EQUITY:44682 TOT_PROFIT:34682 DD:0.0% MDD:16.7% TOT_TRADE:29 WIN%:48.3% P/L:4.9
    # 2019 TOT_EQUITY:29607 TOT_PROFIT:19607 DD:8.7% MDD:15.4% TOT_TRADE:26 WIN%:38.5% P/L:5.3
    year = 2019
    bot = Bot(api, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
              candle_period='1h',
              backtest=True, test_start=f'{year}-01-01', test_end=f'{year}-12-31',
              test_data='../candle_data/BINANCE_BTCUSDT, 60.csv'
              # test_data='../candle_data/BITFINEX_BTCUSD, 120.csv'
              # test_data='../candle_data/BINANCE_ETCUSDT, 60.csv'
              # test_data='../candle_data/BITFINEX_ETHUSD, 60.csv'
              ,
              telegram_bot_token='852670167:AAExawLUJfb-lGKVHQkT5mthCTEOT_BaQrg',
              telegram_chat_id='352354994'
              )

    algo = AlertGo(week_start=Yoil.MON, hour_start=0, long_rate=0.4, short_rate=0.4)
    asyncio.run(bot.run(algo))
