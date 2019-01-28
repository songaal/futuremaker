from datetime import datetime
import os
import sys

from futuremaker import indicators, utils
from futuremaker.algo import Algo
from futuremaker.bitmex.bot import Bot
from futuremaker.indicators import heikinashi
from futuremaker.log import logger
import talib as ta

VERSION = '1.0.0'


class HeiGo(Algo):

    def __init__(self, params):
        self.symbol = params['symbol']
        logger.info('%s created!', self.__class__.__name__)

        # 상태.
        self.s = {
            'tobe_long': False,
            'tobe_short': False,
            'long_entry': None,
            'short_entry': None,
            'trade': 0,
            'order': 0,
        }

    def update_candle(self, df, candle):
        # logger.info('update_candle %s > %s : %s', df.index[-1], df.iloc[-1], candle)
        logger.info('>> %s >> %s', datetime.fromtimestamp(df.index[-1] / 1000),
                    f"O:{candle['open']} H:{candle['high']} L:{candle['low']} C:{candle['close']} V:{candle['volume']}")

        hei = heikinashi(df)
        logger.info('Enter..')
        self.enter(df, hei)
        logger.info('Leave..')
        self.leave(df, hei)
        logger.info('Done..')
        # 다음 캔들이 도착할때까지 체결못하면 취소하고 다시 시도.
        # if self.tobe_long:
        #     pass
        #
        # elif self.tobe_short:
        #     pass

        # 체결안된 오더가 있다면 취소 또는 가격을 조정한다.

    def update_order(self, order):
        logger.info('update_order > %s', order)

    def update_position(self, position):
        logger.info('update_position > %s', position)

    def enter(self, df, hei):
        if self.s['long_entry'] is None and self.s['short_entry'] is None:
            if hei.HA_Diff.iloc[-1] > 0 and hei.HA_Diff.iloc[-2] > 0:
                # 가격이 높아지는 추세.
                if hei.HA_Diff.iloc[-1] + hei.HA_Diff.iloc[-2] >= 1:
                    # 롱 진입.
                    self.s['long_entry'] = hei.HA_Close.iloc[-1]
                    self.s['order'] += 1
                    logger.info('롱 진입요청 @%s', df.Close.iloc[-1])
            elif hei.HA_Diff.iloc[-1] < 0 and hei.HA_Diff.iloc[-2] < 0:
                # 가격이 낮아지는 추세.
                if hei.HA_Diff.iloc[-1] + hei.HA_Diff.iloc[-2] <= -1:
                    # 숏 진입.
                    self.s['short_entry'] = hei.HA_Close.iloc[-1]
                    self.s['order'] += 1
                    logger.info('숏 진입요청 @%s', df.Close.iloc[-1])

    def leave(self, df, hei):
        N = 3  # 3개의 연속 가격을 확인하여 익절.
        close = hei.HA_Close.iloc[-1]
        if self.s['short_entry'] is not None:
            # 숏 청산.
            if hei.HA_Diff.iloc[-1] > 0 or self.great_or_eq(hei.HA_Close, N):
                tobe_pnl = self.s['short_entry'] - close
                self.s['order'] += 1
                logger.info('숏 청산요청 @%s pnl[%s]', df.Close.iloc[-1], tobe_pnl)

        elif self.s['long_entry'] is not None:
            # 롱 청산.
            if hei.HA_Diff.iloc[-1] < 0 or self.less_or_eq(hei.HA_Close, N):
                tobe_pnl = close - self.s['long_entry']
                self.s['order'] += 1
                logger.info('롱 청산요청 @%s pnl[%s]', df.Close.iloc[-1], tobe_pnl)

    def less_or_eq(self, list, size):
        prev_val = None
        for val in list[-size:]:
            if prev_val and val > prev_val:
                return False
            prev_val = val
        return True

    def great_or_eq(self, list, size):
        prev_val = None
        for val in list[-size:]:
            if prev_val and val < prev_val:
                return False
            prev_val = val
        return True


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    exchange = params['exchange']
    symbol = params['symbol']
    candle_period = params['period']
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

    bot = Bot(exchange=exchange, symbol=symbol, leverage=leverage, candle_limit=candle_limit,
              candle_period=candle_period, api_key=api_key, api_secret=api_secret,
              testnet=testnet, dry_run=dry_run, telegram_bot_token=telegram_bot_token,
              telegram_chat_id=telegram_chat_id, http_port=http_port, backtest=backtest, test_start=test_start, test_end=test_end)

    algo = HeiGo(params)
    bot.run(algo)
