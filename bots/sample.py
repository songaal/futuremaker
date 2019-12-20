import sys

from futuremaker import utils
from futuremaker.bitmex.bitmex_ws import BitmexWS
from futuremaker.bot import Bot
from futuremaker.algo import Algo


class AlertGo(Algo):

    def update_candle(self, df, candle):
        print('update_candle %s > ', df.index[-1], df.iloc[-1], candle)


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    api = utils.ccxt_exchange('bitmex', api_key='05y_4aALSt-BrVgnNhSfhppP', api_secret=params['api_secret'],
                              is_async=False, testnet=True)
    # api.private_post_position_leverage({'symbol': symbol, 'leverage': leverage})
    ws = BitmexWS('XBT/USD', candle_period='1m',
                  api_key='05y_4aALSt-BrVgnNhSfhppP', api_secret=params['api_secret'],
                  testnet=True)

    bot = Bot(api, ws, symbol='XBT/USD', candle_limit=20,
              candle_period='1m', testnet=True,
              api_key='05y_4aALSt-BrVgnNhSfhppP', api_secret=params['api_secret'],
              # leverage=1,
              # dry_run=dry_run, telegram_bot_token=telegram_bot_token,
              # telegram_chat_id=telegram_chat_id, http_port=http_port, backtest=backtest, test_start=test_start,
              # test_end=test_end
              )

    algo = AlertGo()
    bot.run(algo)
