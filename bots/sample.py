import sys

from futuremaker import utils
from futuremaker.bitmex.bitmex_ws import BitmexWS
from futuremaker.bot import Bot
from futuremaker.algo import Algo
import pandas as pd

class AlertGo(Algo):

    def update_candle(self, df, candle):
        print('update_candle > ', df.index[-1], candle.name)
        print(candle)


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

    bot = Bot(api, symbol='BTCUSDT', candle_limit=24 * 7,
              candle_period='1h',
              backtest=True, test_start='2019-01-01',
              test_data='../candle_data/BINANCE_BTCUSDT, 60.csv'
              )

    algo = AlertGo()
    bot.run(algo)
