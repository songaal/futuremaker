import sys
from enum import Enum, auto

from futuremaker import utils
from futuremaker.bitmex.bitmex_ws import BitmexWS
from futuremaker.bot import Bot
from futuremaker.algo import Algo
import pandas as pd


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
        self.started = False
        self.this_week = -1
        self.prev_week_candle = None
        self.week_candle = {'open': -1, 'high': -1, 'low': -1}


    def prepare_week_candle(self, df):
        pass

        # print('Prev week high, low > ', high, low)

    def prepare_week_candle_old(self, df):
        status = 0
        high = -1
        low = -1
        for i in range(24 * 7 * 2):
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
            # df.iloc[-1].
            pass
            # 하나씩 지표들을 완성해감.

        # Monday 0 ~ Sunday 6
        # print('요일: ', candle.name.dayofweek)

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
