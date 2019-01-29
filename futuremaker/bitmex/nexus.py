import datetime

from futuremaker import utils
from futuremaker.bitmex_ws import BitmexWS
from futuremaker.candle_handler import CandleHandler
from futuremaker.log import logger


class Nexus(object):
    """
    거래소의 상태를 모두 가지고 있는 매우 중요한 객체.
    포지션, 주문, 잔고등이 웹소켓을 통해 지속적으로 업데이트 된다.
    물론 캔들데이터도 저장된다.
    주문기능도 가지고 있다.
    nexus.api.put_order() 와 같이 사용.
    """

    def __init__(self, exchange, symbol, leverage=None, api_key=None, api_secret=None, testnet=True, dry_run=False,
                 candle_limit=None, candle_period=None):
        """
        :param exchange: 거래소이름. bitmex, bithumb..
        :param symbol: 심볼페어. XBTUSD, BTC/USD
        :param dry_run: 참일 경우 실제 주문 api를 호출하지 않는다.
        :param candle_limit: 저장할 최대 캔들갯수.
        :param candle_period: 봉주기. Bitmex는 4가지만 지원한다. 1m, 5m, 1h, 1d
        """
        self.candle_handler = None
        raw_symbol = symbol.replace('/', '')
        self.api = utils.ccxt_exchange(exchange, api_key=api_key, api_secret=api_secret, is_async=False, opt={'test':testnet})
        if api_key and api_secret and self.api and leverage is not None:
            self.api.private_post_position_leverage({'symbol': raw_symbol, 'leverage': leverage})

        logger.info('>>candle_period>> %s',candle_period)
            # 웹소켓 처리기.
        self.ws = BitmexWS(raw_symbol, candle_period,
                           api_key=api_key,
                           api_secret=api_secret,
                           testnet=testnet)

        if candle_limit and candle_period:
            period_in_second = 0
            if candle_period == '1m':
                period_in_second = 60
            elif candle_period == '5m':
                period_in_second = 300
            elif candle_period == '1h':
                period_in_second = 3600
            elif candle_period == '1d':
                period_in_second = 3600 * 24
            since = datetime.datetime.now().timestamp() - period_in_second * candle_limit
            since = since * 1000
            self.candle_handler = CandleHandler(self.api, symbol, period=candle_period, history=candle_limit, since=since)

    def callback(self, update_orderbook=None, update_candle=None, update_order=None, update_position=None):
        """
        데이터 변경시 호출되는 콜백함수들을 설정한다.
        :param update_orderbook: 호가창 업데이트시마다 호출. 매우 빈번히 호출.
        :param update_candle: 캔들업데이트시 호출되는 콜백함수. 캔들의 period 마다 호출된다.
        :param update_order: 주문이 성공되거나 할때 호출되는 콜백함수
        :param update_position: 포지션 변경시 호출되는 콜백함수
        :return:
        """
        self.cb_update_candle = update_candle
        self.ws.update_orderbook = update_orderbook
        self.ws.update_candle = self._update_candle
        self.ws.update_order = update_order
        self.ws.update_position = update_position

    def _update_candle(self, item):
        candle_df = self.candle_handler.update(item)
        # 캔들업뎃호출
        if self.cb_update_candle:
            self.cb_update_candle(candle_df, item)

    async def load(self):
        try:

            # await
            self.api.load_markets()

            if self.candle_handler:
                # await
                self.candle_handler.load()
            else:
                logger.info('candle_handler 를 사용하지 않습니다.')

            await self.ws.connect()
        except:
            utils.print_traceback()

    async def start(self):
        await self.ws.listen()

    async def wait_ready(self):
        await self.ws.wait_ready()

    def __getitem__(self, item):
        if item in self.ws.data:
            return self.ws.data[item]