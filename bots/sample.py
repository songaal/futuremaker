import sys
from futuremaker import utils
from futuremaker.bot import Bot
from futuremaker.algo import Algo
import pandas as pd
import numpy as np
from futuremaker import log


class Yoil:
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6


class IndicatorGenerator:

    def update(self, df, candle):
        return df.iloc[-1]


class WeekIndicator(IndicatorGenerator):
    def __init__(self, week_start, hour_start, long_rate, short_rate):
        self.week_start = week_start
        self.hour_start = hour_start
        self.long_rate = long_rate
        self.short_rate = short_rate

        self.started = False
        self.this_week = -1
        self.prev_week_candle = None
        self.week_candle = {'open': -1, 'high': -1, 'low': -1}
        self.count = 0

        self.week_open_price = np.NaN
        self.week_high = np.NaN
        self.week_low = np.NaN
        self.long_price = np.NaN
        self.short_price = np.NaN

    def update(self, df, candle):
        if not self.started:
            # 초기화
            self.__prepare_indicator(df)
            self.started = True
        else:
            # 하나씩 지표들을 완성해감.
            self.__append_indicator(df.index[-1], df, candle)
        return df.iloc[-1]

    def __prepare_indicator(self, df):
        # 1. 돌파가격을 계산한다.
        for i in range(len(df.index)):
            index = df.index[i]
            candle = df.iloc[i]
            self.__append_indicator(index, df, candle)

    def __append_indicator(self, index, df, candle):
        today = candle.name
        if today.hour == self.hour_start and today.dayofweek == self.week_start:
            # week 의 시작을 만나고 기준시각일때 한번만 계산.
            self.week_open_price = candle.open
            # 새로 한주가 시작되었다면 이전에 만들어 놓은 high, low를 돌파변수로 이용한다.
            volatility = self.week_high - self.week_low
            self.week_high = np.NaN
            self.week_low = np.NaN
            self.long_price = self.week_open_price + self.long_rate * volatility
            self.short_price = self.week_open_price - self.short_rate * volatility
            # print('WEEK OPENED > ', index, ', week_open_price: ', self.week_open_price, ', volat: ', volatility)

        # 매시간 계산.
        self.week_high = np.nanmax([self.week_high, candle.high])
        self.week_low = np.nanmin([self.week_low, candle.low])

        # 2. 돌파가격 리스트를 시리즈로 넣는다.
        df.loc[index, 'week_open_price'] = self.week_open_price
        df.loc[index, 'long_break'] = self.long_price
        df.loc[index, 'short_break'] = self.short_price
        # print(index, candle.high, candle.low, self.week_open_price, self.long_price, self.short_price)


class AlertGo(Algo):

    def __init__(self):
        self.pyramiding = 1
        self.init_capital = 10000
        self.default_amount = self.init_capital * 0.8
        self.long_amount = 0
        self.long_entry_price = 0
        self.long_entry_time = None
        self.short_amount = 0
        self.short_entry_price = 0
        self.short_entry_time = None
        self.total_profit = 0.0
        self.total_trade = 0
        self.win_trade = 0
        self.lose_trade = 0

        week_start = Yoil.MON
        hour_start = 0
        long_rate = 0.4
        short_rate = 0.4

        self.weekIndicator = WeekIndicator(week_start, hour_start, long_rate, short_rate)

    def update_candle(self, df, candle):
        time = candle.name
        candle = self.weekIndicator.update(df, candle)

        # candle 이 long_break 를 뚫으면.
        if candle.open < candle.long_break < candle.close:
            # if candle.close - candle.open > 50:
            if self.long_amount == 0:
                if self.short_amount > 0:
                    # 하루이상 지나야 매매한다.
                    if (time - self.short_entry_time).days >= 1:
                        # 이익 확인.
                        profit = self.short_amount * (-(candle.close - self.short_entry_price) / self.short_entry_price)
                        log.position.info(f'{time} CLOSE SHORT {self.short_amount}@{candle.close} PROFIT: {profit}')
                        self.total_profit += profit
                        # trade 횟수.
                        self.total_trade += 1
                        if profit > 0:
                            self.win_trade += 1
                        else:
                            self.lose_trade += 1
                        # 초기화
                        self.short_amount = 0
                        # 요약
                        self.show_summary()

            if self.short_amount == 0 and self.long_amount == 0:
                log.position.info(f'{time} OPEN LONG {self.default_amount}@{candle.close}')
                self.long_amount += self.default_amount
                self.long_entry_price = candle.close
                self.long_entry_time = time

        if candle.close < candle.short_break < candle.open:
            # short 수행.
            if self.short_amount == 0:
                if self.long_amount > 0:
                    if (time - self.long_entry_time).days >= 1:
                        # 이익 확인.
                        profit = self.long_amount * ((candle.close - self.long_entry_price) / self.long_entry_price)
                        log.position.info(f'{time} CLOSE LONG {self.long_amount}@{candle.close} PROFIT: {profit}')
                        self.total_profit += profit
                        # trade 횟수.
                        self.total_trade += 1
                        if profit > 0:
                            self.win_trade += 1
                        else:
                            self.lose_trade += 1
                        # 초기화
                        self.long_amount = 0
                        # 요약
                        self.show_summary()

            if self.short_amount == 0 and self.long_amount == 0:
                log.position.info(f'{time} OPEN SHORT {self.default_amount}@{candle.close}')
                self.short_amount += self.default_amount
                self.short_entry_price = candle.close
                self.short_entry_time = time

    def show_summary(self):
        log.position.info(f'SUMMARY TOT_PROFIT: {self.total_profit:.0f} TOT_TRADE: {self.total_trade} WIN%: {(self.win_trade / self.total_trade) * 100 if self.total_trade > 0 else 0:2.1f}%')


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

    bot = Bot(api, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
              candle_period='1h',
              backtest=True, test_start='2019-01-01',
              test_data='../candle_data/BINANCE_BTCUSDT, 60.csv'
              )

    algo = AlertGo()
    bot.run(algo)
