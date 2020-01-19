from datetime import datetime
import os
import sys

from futuremaker import indicators, utils
from futuremaker.algo import Algo
from futuremaker.bitmex.bitmex_ws import BitmexWS
from futuremaker.bot import Bot
from futuremaker.log import logger

VERSION = '1.0.0'


class AlertGo(Algo):

    def __init__(self, params):
        self.symbol = params['symbol']
        logger.info('%s created!', self.__class__.__name__)

    def update_candle(self, df, candle):
        # logger.info('update_candle %s > %s : %s', df.index[-1], df.iloc[-1], candle)
        logger.info('>> %s >> %s', datetime.fromtimestamp(df.index[-1] / 1000),
                    f'O:{candle.Open} H:{candle.High} L:{candle.Low} C:{candle.Close} V:{candle.Volume}')
        price = df.Close.iloc[-1]
        m, u, l = indicators.bollinger_bands(df.Close, n=20, stdev=1.5)

        high = round(u.iloc[-1], 2)
        low = round(l.iloc[-1], 2)
        logger.info('BBands high[%s] price[%s] low[%s]', high, price, low)
        df = indicators.RSI(df, period=14)
        rsi = df.RSI.iloc[-1]
        rsi = round(rsi, 2)
        logger.info('RSI[%s]', rsi)

        score = 0
        if price >= high:
            logger.info('BBands Upper touched! price[%s] >= bbhigh[%s]', price, high)
            score += 1
        elif price <= low:
            logger.info('BBands Lower touched! price[%s] <= bblow[%s]', price, low)
            score -= 1

        if rsi >= 60:
            logger.info('RSI[%s] >= 60.', rsi)
            score += 1
        elif rsi <= 40:
            logger.info('RSI[%s] <= 40.', rsi)
            score -= 1

        if score >= 2:
            self.send_telegram(f'{self.symbol} Too much buy! price[{price}] >= bbhigh[{high}] AND RSI[{rsi}] >= 60')
        elif score <= -2:
            self.send_telegram(f'{self.symbol} Too much sell! price[{price}] <= bblow[{low}] AND RSI[{rsi}] <= 40')

        sys.exit(0)

    def update_order(self, order):
        logger.info('update_order > %s', order)

    def update_position(self, position):
        logger.info('update_position > %s', position)


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    exchange = params['exchange']
    symbol = params['symbol']
    candle_period = params['candle_period']
    http_port = params['http_port']
    backtest = params['backtest'] == 'True'
    test_start = params['test_start']
    test_end = params['test_end']
    if test_start:
        test_start = datetime.strptime(test_start, '%Y-%m-%d %H:%M:%S%z')
    if test_end:
        test_end = datetime.strptime(test_end, '%Y-%m-%d %H:%M:%S%z')
    leverage = 1
    candle_limit = 20
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    testnet = os.getenv('TESTNET') == 'True'
    dry_run = os.getenv('DRY_RUN') == 'True'

    api = utils.ccxt_exchange(exchange, api_key=api_key, api_secret=api_secret, is_async=False, testnet=testnet)
    api.private_post_position_leverage({'symbol': symbol, 'leverage': leverage})
    ws = BitmexWS(symbol, candle_period,
                  api_key=api_key,
                  api_secret=api_secret,
                  testnet=testnet)

    bot = Bot(api, ws, symbol=symbol, leverage=leverage, candle_limit=candle_limit,
              candle_period=candle_period, dry_run=dry_run, telegram_bot_token=telegram_bot_token,
              telegram_chat_id=telegram_chat_id, http_port=http_port, backtest=backtest, test_start=test_start,
              test_end=test_end)

    algo = AlertGo(params)
    bot.run(algo)
