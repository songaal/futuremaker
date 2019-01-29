from datetime import datetime
import os
import sys

from futuremaker import utils
from futuremaker.algo import Algo
from futuremaker.bitmex.bot import Bot
from futuremaker.indicators import heikinashi
from futuremaker.log import logger

VERSION = '1.0.0'


class HeiGo(Algo):

    def __init__(self, params):
        self.symbol = params['symbol']
        self.amount = int(params['amount'])  # 계약 갯수.
        self.stoploss = int(params['stoploss'])  # 손절범위. 달러.
        logger.info('%s created!', self.__class__.__name__)

        # 상태.
        self.s = {
            'current_qty': 0,
            'entry_price': 0,
            'order': 0,
        }

    def update_candle(self, df, candle):
        # logger.info('update_candle %s > %s : %s', df.index[-1], df.iloc[-1], candle)
        logger.info('>> %s >> %s', datetime.fromtimestamp(df.index[-1] / 1000),
                    f"O:{candle['open']} H:{candle['high']} L:{candle['low']} C:{candle['close']} V:{candle['volume']}")
        logger.info('orders > %s', self.data['order'])
        logger.info('self.s > %s', self.s)
        for order in self.data['order']:
            # limit 주문만 수정. stop은 손절주문이므로 수정하지 않으며, update_position에서 수정함.
            if order['ordType'] == 'Limit' and order['leavesQty'] > 0:
                price = order['price']
                order_id = order['orderID']
                if order['side'] == 'Sell':
                    ask1 = self.data['orderBook10'][0]['asks'][0]
                    if abs(ask1[0] - price) >= 1:  # 3틱이상 밀리면 취소.
                        # 1달러보다 벌어지면 취소.
                        self.api.cancel_order(id=order_id, symbol=symbol)
                elif order['side'] == 'Buy':
                    bid1 = self.data['orderBook10'][0]['bids'][0]
                    if abs(bid1[0] - price) >= 1:  # 3틱이상 밀리면 취소.
                        self.api.cancel_order(id=order_id, symbol=symbol)

        hei = heikinashi(df)
        logger.info('Enter..')
        self.enter(df, hei)
        logger.info('Leave..')
        self.leave(df, hei)
        logger.info('Done..')
        # 다음 캔들이 도착할때까지 체결못하면 취소하고 다시 시도.

        # 체결안된 오더가 있다면 취소 또는 가격을 조정한다.

    def update_order(self, order):
        logger.info('update_order > %s', order)

    def update_position(self, position):
        logger.info('update_position > %s', position)
        self.s['current_qty'] = position['currentQty']
        current_qty = self.s['current_qty']

        if current_qty == 0:
            # stop모두 취소.
            for order in self.data['order']:
                # limit 주문만 수정. stop은 손절주문이므로 수정하지 않으며, update_position에서 수정함.
                if order['ordType'] == 'Stop':
                    order_id = order['orderID']
                    self.api.cancel_order(id=order_id, symbol=symbol)
            return

        if 'avgEntryPrice' in position:
            if position['avgEntryPrice']:
                self.s['entry_price'] = position['avgEntryPrice']
                if current_qty > 0:
                    # 롱 포지션은 아래쪽에 Sell을 예약한다.
                    stop_price = round(self.s['entry_price'] - self.stoploss)
                    found = False
                    for order in self.data['order']:
                        # limit 주문만 수정. stop은 손절주문이므로 수정하지 않으며, update_position에서 수정함.
                        if order['ordType'] == 'Stop' and order['side'] == 'Sell':
                            order_id = order['orderID']
                            self.api.edit_order(id=order_id, symbol=symbol, type='Stop', side='Buy',
                                                amount=abs(current_qty),
                                                params={'execInst': 'Close,LastPrice', 'stopPx': stop_price})
                            found = True
                            break
                    if not found:
                        self.api.create_order(symbol, type='Stop', side='Sell',
                                              amount=abs(current_qty),
                                              params={'execInst': 'Close,LastPrice', 'stopPx': stop_price})
                elif current_qty < 0:
                    # 숏 포지션은 위쪽에 Buy를 예약한다.
                    stop_price = round(self.s['entry_price'] + self.stoploss)
                    found = False
                    for order in self.data['order']:
                        # limit 주문만 수정. stop은 손절주문이므로 수정하지 않으며, update_position에서 수정함.
                        if order['ordType'] == 'Stop' and order['side'] == 'Buy':
                            order_id = order['orderID']
                            self.api.edit_order(id=order_id, symbol=symbol, type='Stop', side='Sell',
                                                amount=abs(current_qty),
                                                params={'execInst': 'Close,LastPrice', 'stopPx': stop_price})
                            found = True
                            break
                    if not found:
                        self.api.create_order(symbol, type='Stop', side='Buy',
                                              amount=abs(current_qty),
                                              params={'execInst': 'Close,LastPrice', 'stopPx': stop_price})

    def enter(self, df, hei):
        # 포지션이 없을때만
        if self.s['current_qty'] == 0:
            if hei.HA_Diff.iloc[-1] > 0 and hei.HA_Diff.iloc[-2] > 0:
                # 가격이 높아지는 추세.
                if hei.HA_Diff.iloc[-1] + hei.HA_Diff.iloc[-2] >= 1:
                    # 롱 진입.
                    self.s['order'] += 1
                    logger.info('롱 진입요청 @%s', df.Close.iloc[-1])
                    self.buy_orderbook1(self.amount)

            elif hei.HA_Diff.iloc[-1] < 0 and hei.HA_Diff.iloc[-2] < 0:
                # 가격이 낮아지는 추세.
                if hei.HA_Diff.iloc[-1] + hei.HA_Diff.iloc[-2] <= -1:
                    # 숏 진입.
                    self.s['order'] += 1
                    logger.info('숏 진입요청 @%s', df.Close.iloc[-1])
                    self.sell_orderbook1(self.amount)

    def leave(self, df, hei):
        N = 3  # 3개의 연속 가격을 확인하여 익절.
        close = hei.HA_Close.iloc[-1]
        if self.s['current_qty'] < 0:
            # 숏 청산.
            if hei.HA_Diff.iloc[-1] > 0 or self.great_or_eq(hei.HA_Close, N):
                tobe_pnl = self.s['entry_price'] - close
                self.s['order'] += 1
                logger.info('숏 청산요청 @%s tobe_pnl[%s]', df.Close.iloc[-1], tobe_pnl)
                self.s['short_entry'] = None
                self.buy_orderbook1(self.s['current_qty'], reduce_only=True)

        elif self.s['current_qty'] > 0:
            # 롱 청산.
            if hei.HA_Diff.iloc[-1] < 0 or self.less_or_eq(hei.HA_Close, N):
                tobe_pnl = close - self.s['entry_price']
                self.s['order'] += 1
                logger.info('롱 청산요청 @%s tobe_pnl[%s]', df.Close.iloc[-1], tobe_pnl)
                self.s['long_entry'] = None
                self.sell_orderbook1(self.s['current_qty'], reduce_only=True)

    def buy_orderbook1(self, amount, reduce_only=False):
        bid1 = self.data['orderBook10'][0]['bids'][0]
        limit_price, limit_volume = bid1[0], bid1[1]
        params = {'execInst': 'ParticipateDoNotInitiate'}
        if reduce_only:
            params = {'execInst': 'ParticipateDoNotInitiate,Close'}
        self.api.create_order(symbol, type='limit', side='buy',
                              price=limit_price, amount=abs(amount),
                              params=params)

    def sell_orderbook1(self, amount, reduce_only=False):
        ask1 = self.data['orderBook10'][0]['asks'][0]
        limit_price, limit_volume = ask1[0], ask1[1]
        params = {'execInst': 'ParticipateDoNotInitiate'}
        if reduce_only:
            params = {'execInst': 'ParticipateDoNotInitiate,Close'}
        self.api.create_order(symbol, type='limit', side='sell',
                              price=limit_price, amount=abs(amount),
                              params=params)

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
    amount = params['amount']
    leverage = params['leverage']
    stoploss = params['stoploss']
    http_port = params['http_port']
    backtest = params['backtest'] == 'True'
    test_start = params['test_start']
    test_end = params['test_end']
    if test_start:
        test_start = datetime.strptime(test_start, '%Y-%m-%d %H:%M:%S%z')
    if test_end:
        test_end = datetime.strptime(test_end, '%Y-%m-%d %H:%M:%S%z')
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
              telegram_chat_id=telegram_chat_id, http_port=http_port, backtest=backtest, test_start=test_start,
              test_end=test_end)

    algo = HeiGo(params)
    bot.run(algo)
