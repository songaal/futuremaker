from futuremaker.bitmex.algo import Algo

class AlertGo(Algo):

    def __init__(self):
        super(AlertGo, self).__init__(symbol="XBTUSD", candle_limit=20, candle_period="1m")

    def update_candle(self, df, candle):
        print('update_candle %s > ', df.index[-1], df.iloc[-1], candle)


if __name__ == '__main__':
    bot = AlertGo()
    bot.run()
