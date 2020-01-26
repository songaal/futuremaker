import sys
from futuremaker import utils
from futuremaker.bot import Bot
from futuremaker.algo import Algo
import pandas as pd
import numpy as np


class Yoil:
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6


class AlertGo(Algo):

    def __init__(self):
        self.week_start = Yoil.TUE
        self.hour_start = 0
        self.long_rate = 0.4
        self.short_rate = 0.4

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

    def update_candle(self, df, candle):
        if not self.started:
            # 초기화
            self.prepare_indicator(df)
            self.started = True
            # sys.exit(1)
        else:
            # 하나씩 지표들을 완성해감.
            index = df.index[-1]
            self.append_indicator(index, df, candle)
        #     self.count += 1
        #     if self.count > 2000:
        #         sys.exit(1)

    def prepare_indicator(self, df):
        # 1. 돌파가격을 계산한다.
        for i in range(len(df.index)):
            index = df.index[i]
            candle = df.iloc[i]
            self.append_indicator(index, df, candle)
        print(df)

    def append_indicator(self, index, df, candle):
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


class ExchangeAPI:
    def __init__(self):
        self.data = {}


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])

    # api 에 key와 secret 을 모두 셋팅.
    # api 는 오더도 가능하지만 캔들정보도 확인가능. 1분마다 확인.
    api = None

    # telegram_bot_token=telegram_bot_token,
    # telegram_chat_id=telegram_chat_id,
    alert = None
    api = ExchangeAPI()

    bot = Bot(api, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
              candle_period='1h',
              backtest=True, test_start='2019-01-01',
              test_data='../candle_data/BINANCE_BTCUSDT, 60.csv'
              )

    algo = AlertGo()
    bot.run(algo)
