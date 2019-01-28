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

        self.tobe_long = False
        self.tobe_short = False

    def update_candle(self, df, candle):
        # logger.info('update_candle %s > %s : %s', df.index[-1], df.iloc[-1], candle)
        logger.info('>> %s >> %s', datetime.fromtimestamp(df.index[-1] / 1000),
                    f'O:{candle.Open} H:{candle.High} L:{candle.Low} C:{candle.Close} V:{candle.Volume}')

        # 다음 캔들이 도착할때까지 체결못하면 취소하고 다시 시도.
        if self.tobe_long:
            pass

        elif self.tobe_short:
            pass

        # 체결안된 오더가 있다면 취소 또는 가격을 조정한다.
        if not self.tobe_long and not self.tobe_short:
            self.algo(df)


    def update_order(self, order):
        logger.info('update_order > %s', order)

    def update_position(self, position):
        logger.info('update_position > %s', position)

    def algo(self, data):
        ha = heikinashi(data)

        prev_diff = 0
        trade = 0
        entry_idx = None
        long_entry = None
        short_entry = None
        total_pnl = 0
        r_index = []
        r_value = []
        close_list = []
        ha_close_list = []
        N = 3  # 3개의 연속 가격을 확인하여 익절.
        for diff, ha_close, close, idx in zip(ha.HA_Diff, ha.HA_Close, data.Close, data.index):
            pnl = 0
            # plt.axvspan(prev_ts, ts, facecolor='g' if prev_type == 'U' else 'r', alpha=0.5)

            close_list.append(close)
            close_list = close_list[-N:]

            ha_close_list.append(ha_close)
            ha_close_list = ha_close_list[-N:]

            if short_entry is not None:
                # 숏 청산.
                if diff > 0 or self.great_or_eq(ha_close_list):
                    pnl = short_entry - close
                    total_pnl += pnl
                    elapsed = idx - entry_idx
                    r_index.append(idx)
                    r_value.append(total_pnl)
                    trade += 1
                    logger.info('[%s] TOTAL_PNL[%s] PNL[$%s] SEC[%s] Price[%s->%s] Time[%s~%s]', trade, total_pnl, pnl,
                                elapsed.seconds, short_entry,
                                close, entry_idx, idx)
                    short_entry = None

            elif long_entry is not None:
                if diff < 0 or self.less_or_eq(ha_close_list):
                    pnl = close - long_entry
                    total_pnl += pnl
                    elapsed = idx - entry_idx
                    r_index.append(idx)
                    r_value.append(total_pnl)
                    trade += 1
                    logger.info('[%s] TOTAL_PNL[%s] PNL[$%s] SEC[%s] Price[%s->%s] Time[%s~%s]', trade, total_pnl, pnl,
                                elapsed.seconds, long_entry,
                                close, entry_idx, idx)
                    long_entry = None

            # 청산하고 바로 다시 진입도 가능하다.
            if long_entry is None and short_entry is None:
                if diff > 0 and prev_diff > 0:
                    # 가격이 높아지는 추세.
                    # if close_list[-2] < close_list[-1]:
                    if prev_diff + diff >= 1:
                        # 롱 진입.
                        long_entry = close
                        entry_idx = idx
                        trade += 1
                        self.tobe_long = close
                elif diff < 0 and prev_diff < 0:
                    # 가격이 낮아지는 추세.
                    # if close_list[-2] > close_list[-1]:
                    if prev_diff + diff <= -1:
                        # 숏 진입.
                        short_entry = close
                        entry_idx = idx
                        trade += 1
                        self.tobe_short = close

            prev_diff = diff


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

    bot = Bot(exchange=exchange, symbol=symbol, leverage=leverage, candle_limit=candle_limit,
              candle_period=candle_period, api_key=api_key, api_secret=api_secret,
              testnet=testnet, dry_run=dry_run, telegram_bot_token=telegram_bot_token,
              telegram_chat_id=telegram_chat_id, http_port=http_port, backtest=backtest, test_start=test_start, test_end=test_end)

    algo = HeiGo(params)
    bot.run(algo)
