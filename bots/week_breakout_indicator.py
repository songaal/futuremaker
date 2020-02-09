import numpy as np


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
            print('WEEK OPENED > ', index, ', week_open_price: ', self.week_open_price, ', volat: ', volatility, self.short_price, '~', self.long_price)

        # 매시간 계산.
        self.week_high = np.nanmax([self.week_high, candle.high])
        self.week_low = np.nanmin([self.week_low, candle.low])

        # 2. 돌파가격 리스트를 시리즈로 넣는다.
        df.loc[index, 'week_open_price'] = self.week_open_price
        df.loc[index, 'long_break'] = self.long_price
        df.loc[index, 'short_break'] = self.short_price
        print(f'Append > {index} H[{candle.high}] L[{candle.low}] WeekOpen[{self.week_open_price}] LONG[{self.long_price}] SHORT[{self.short_price}]')
