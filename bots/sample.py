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
        self.start_week = Yoil.TUE
        self.rate = 0.4

        self.started = False
        self.this_week = -1
        self.prev_week_candle = None
        self.week_candle = {'open': -1, 'high': -1, 'low': -1}

    def prepare_week_candle(self, df):

        this_week = -1
        week_open_price = np.NaN
        high = np.NaN
        low = np.NaN
        upper_price = np.NaN
        bottom_price = np.NaN

        df['week_low'] = np.NaN
        for i in range(len(df.index)):
            candle = df.iloc[i]
            dayofweek = df.index[i].dayofweek
            if this_week != dayofweek:
                this_week = dayofweek
                if dayofweek == self.start_week:
                    week_open_price = candle.open
                    # 새로 한주가 시작되었다면 이전에 만들어 놓은 high, low를 돌파변수로 이용한다.
                    volatility = high - low
                    high = np.NaN
                    low = np.NaN
                    upper_price = week_open_price + self.rate * volatility
                    bottom_price = week_open_price - self.rate * volatility
                    print('WEEK OPENED > ', df.index[i], ', week: ', this_week, ', week_open_price: ', week_open_price,
                          ', volat: ', volatility)
            # print(df.index[i], 'WEEK OPEN: ',  week_open_price, ', VOLAT: ', volatility)
            # print(df.index[i], ' UPPER: ',upper_price, ', BOTTOM: ', bottom_price)
            # print(df.index[i], candle)
            high = np.nanmax([high, candle.high])
            low = np.nanmin([low, candle.low])
            # print(i, df.index[i], candle.high, candle.low, high, low)
            # print('----')
            # if i == 5000:
            #     break

    def make_indicator(self, candle):
        today = candle.name
        if self.this_week != today.dayofweek:
            # new week 셋팅
            self.this_week = today.dayofweek
            self.prev_week_candle = self.week_candle
            print('New Week! > ', today)
            print('Prev Week candle > ', self.prev_week_candle)
            self.week_candle = {'open': candle.open, 'high': -1, 'low': -1}
        else:
            self.week_candle['high'] = max(self.week_candle['high'], candle.high)
            self.week_candle['low'] = max(self.week_candle['low'], candle.low)
        # if today.dayofweek == Yoil.MON:
        # if today.hour == 0:
        # 주봉 시작
        #
        # print('update_candle > ', df.index[-1])
        # print('월요일!!!!')
        # print(candle)

    def prepare_week_candle_old(self, df):
        status = 0
        high = -1
        low = -1
        for i in range(len(df.index)):
            row = df.iloc[-1 - i - 1]
            date = row.name
            if date.dayofweek == self.start_week:
                status = 1
                target = Yoil.SUN if self.start_week == Yoil.MON else self.start_week - 1

            if status == 1:
                if date.dayofweek == target:
                    status = 2

            if status == 2:
                # candle value check
                high = max(high, row.high)
                low = min(low, row.low)

                if date.dayofweek == self.start_week and date.hour == 0:
                    # 마지막 봉.
                    return high, low

    def update_candle(self, df, candle):
        if not self.started:
            # 초기화
            self.prepare_week_candle(df)
            self.started = True
        else:
            # 하나씩 지표들을 완성해감.
            self.make_indicator(candle)


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
