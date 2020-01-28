import sys
from datetime import datetime

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

    def __init__(self, week_start=Yoil.MON, hour_start=0, long_rate=0.4, short_rate=0.4):
        self.pyramiding = 1
        self.init_capital = 10000
        self.default_amount = self.init_capital * 0.8
        self.long_amount = 0
        self.long_entry_price = 0
        self.long_losscut_price = 0
        # self.long_entry_time = None
        self.short_amount = 0
        self.short_entry_price = 0
        self.short_losscut_price = 0
        # self.short_entry_time = None
        self.position_entry_time = datetime.fromtimestamp(0)
        self.total_profit = 0.0
        self.total_equity = 0
        self.total_trade = 0
        self.win_trade = 0
        self.lose_trade = 0
        self.max_equity = 0
        self.dd = 0
        self.mdd = 0
        self.weekIndicator = WeekIndicator(week_start, hour_start, long_rate, short_rate)

    # TODO
    # 1. 손절하도록. 손절하면 1일후에 집입토록.
    # 2. MDD 측정. 손익비 측정.
    # 3. long rate, short rate 다르게 테스트..
    def update_candle(self, df, candle):
        time = candle.name
        candle = self.weekIndicator.update(df, candle)

        # 1. candle 이 long_break 를 뚫으면 롱 포지션을 취한다.
        if candle.open < candle.long_break < candle.close:
            # 하루이상 지나야 매매한다.
            if (time - self.position_entry_time).days >= 1:
                if self.long_amount == 0:
                    # 먼저 숏 포지션을 CLOSE 한다.
                    if self.short_amount > 0:
                        self.close_position(time, candle.close, self.short_entry_price, -self.short_amount)

                if self.short_amount == 0 and self.long_amount == 0:
                    log.position.info(f'{time} OPEN LONG {self.default_amount}@{candle.close}')
                    self.long_amount += self.default_amount
                    self.long_entry_price = candle.close
                    self.long_losscut_price = candle.long_break
                    self.position_entry_time = time

        # 2. candle 이 short_break 를 뚫으면 숏 포지션을 취한다.
        if candle.close < candle.short_break < candle.open:
            if (time - self.position_entry_time).days >= 1:
                # short 수행.
                if self.short_amount == 0:
                    # 먼저 롱 포지션을 CLOSE 한다.
                    if self.long_amount > 0:
                        self.close_position(time, candle.close, self.long_entry_price, self.long_amount)

                if self.short_amount == 0 and self.long_amount == 0:
                    log.position.info(f'{time} OPEN SHORT {self.default_amount}@{candle.close}')
                    self.short_amount += self.default_amount
                    self.short_entry_price = candle.close
                    self.short_losscut_price = candle.short_break
                    self.position_entry_time = time

        # 3. 롱 포지션 손절.
        if self.long_amount > 0:
            if candle.close < self.long_losscut_price:
                if (time - self.position_entry_time).days >= 1:
                    self.close_position(time, candle.close, self.long_entry_price, self.long_amount)

        # 4. 숏 포지션 손절.
        if self.short_amount > 0:
            if candle.close > self.short_losscut_price:
                if (time - self.position_entry_time).days >= 1:
                    self.close_position(time, candle.close, self.short_entry_price, -self.short_amount)

    def show_summary(self):
        log.position.info(f'SUMMARY TOT_EQUITY:{self.total_equity:.0f} TOT_PROFIT:{self.total_profit:.0f} DD:{self.dd:0.1f}% MDD:{self.mdd:0.1f}% TOT_TRADE:{self.total_trade} WIN%:{(self.win_trade / self.total_trade) * 100 if self.total_trade > 0 else 0:2.1f}% PL%:0')

    def close_position(self, time, exit_price, entry_price, amount):
        # 이익 확인.
        profit = amount * ((exit_price - entry_price) / entry_price)
        log.position.info(f'{time} CLOSE {amount}@{exit_price} PROFIT: {profit}')
        self.total_profit += profit
        self.total_equity = self.init_capital + self.total_profit
        self.max_equity = max(self.max_equity, self.total_equity)
        self.dd = (self.max_equity - self.total_equity) * 100 / self.max_equity if self.max_equity > 0 and self.max_equity - self.total_equity > 0 else 0
        self.mdd = max(self.mdd, self.dd)
        # trade 횟수.
        self.total_trade += 1
        if profit > 0:
            self.win_trade += 1
        else:
            self.lose_trade += 1
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
    api = ExchangeAPI()

    #### MON
    # hour_start=0
    # 2018 SUMMARY TOT_PROFIT: 9768 DD: 0.0% MDD: 33.9% TOT_TRADE: 20 WIN%: 55.0%
    # 2019 SUMMARY TOT_PROFIT: 11654 DD: 2.7% MDD: 7.1% TOT_TRADE: 19 WIN%: 57.9%
    # 손절컷 도입.
    # 2018  SUMMARY TOT_EQUITY:19605 TOT_PROFIT:9605 DD:3.2% MDD:10.6% TOT_TRADE:30 WIN%:36.7% PL%:0
    # 2019 SUMMARY TOT_EQUITY:21251 TOT_PROFIT:11251 DD:3.2% MDD:4.0% TOT_TRADE:27 WIN%:29.6% PL%:0

    # hour=4
    # 2019 SUMMARY TOT_PROFIT: 11583 TOT_TRADE: 19 WIN%: 57.9%

    # hour=9
    # 2018 SUMMARY TOT_PROFIT: 9265 TOT_TRADE: 20 WIN%: 50.0%
    # 2019 SUMMARY TOT_PROFIT: 7967 TOT_TRADE: 19 WIN%: 52.6%

    # hour=12
    # 2018 SUMMARY TOT_PROFIT: 5445 TOT_TRADE: 24 WIN%: 45.8%
    # 2019 SUMMARY TOT_PROFIT: 12126 TOT_TRADE: 18 WIN%: 55.6%

    # hour=17
    # 2018 SUMMARY TOT_PROFIT: 7168 TOT_TRADE: 20 WIN%: 55.0%
    # 2019 SUMMARY TOT_PROFIT: 12632 TOT_TRADE: 16 WIN%: 62.5%

    # hour=23
    # 2018 SUMMARY TOT_PROFIT: 5630 TOT_TRADE: 22 WIN%: 54.5%
    # 2019 SUMMARY TOT_PROFIT: 11041 TOT_TRADE: 20 WIN%: 55.0%

    #### WED
    # hour=0
    # 2018 SUMMARY TOT_PROFIT: 5901 TOT_TRADE: 21 WIN%: 47.6%
    # 2019 SUMMARY TOT_PROFIT: 9571 TOT_TRADE: 20 WIN%: 45.0%

    # hour=9
    # 2019 SUMMARY TOT_PROFIT: 5579 TOT_TRADE: 26 WIN%: 38.5%

    #### FRI
    #hour=0
    # 2019 SUMMARY TOT_PROFIT: 10600 TOT_TRADE: 16 WIN%: 56.2%
    # hour=9
    # 2019 SUMMARY TOT_PROFIT: 4777 TOT_TRADE: 24 WIN%: 41.7%

    #### SUN
    # hour=0
    # 2019 SUMMARY TOT_PROFIT: 5573 TOT_TRADE: 20 WIN%: 45.0%

    # hour=17
    # 2019 SUMMARY TOT_PROFIT: 4617 TOT_TRADE: 22 WIN%: 40.9%

    year = 2018
    bot = Bot(api, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
              candle_period='1h',
              backtest=True, test_start=f'{year}-01-01', test_end=f'{year}-12-31',
              test_data='../candle_data/BINANCE_BTCUSDT, 60.csv'
              )

    algo = AlertGo(week_start=Yoil.MON, hour_start=0, long_rate=0.4, short_rate=0.4)
    bot.run(algo)
