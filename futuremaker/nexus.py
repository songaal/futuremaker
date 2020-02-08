import datetime

from futuremaker import utils
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

    def __init__(self, api, symbol, candle_limit, candle_period=None):
        """
        :param symbol: 심볼페어. XBTUSD, BTC/USD
        :param candle_limit: 저장할 최대 캔들갯수.
        :param candle_period: 봉주기. Bitmex는 4가지만 지원한다. 1m, 5m, 1h, 1d
        """
        self.candle_handler = None
        self.api = api
        self.cb_update_candle = None

        logger.info(f'Nexus symbol[{symbol}] period[{candle_period}]')

        if candle_limit and candle_period:
            period_in_second = 0
            if candle_period == '1m':
                period_in_second = 60
            elif candle_period == '5m':
                period_in_second = 300
            elif candle_period == '10m':
                period_in_second = 600
            elif candle_period == '15m':
                period_in_second = 600
            elif candle_period == '1h':
                period_in_second = 3600
            elif candle_period == '4h':
                period_in_second = 3600 * 4
            elif candle_period == '1d':
                period_in_second = 3600 * 24
            ts = datetime.datetime.now().timestamp() - period_in_second * candle_limit
            since = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:00:00')
            # 현재시각에서 since를 뺀 날짜를 string으로 만든다.
            self.candle_handler = CandleHandler(self.api, symbol, period=candle_period, since=since, _update_notify=self._update_candle)

    def callback(self, update_candle=None):
        """
        데이터 변경시 호출되는 콜백함수들을 설정한다.
        :param update_candle: 캔들업데이트시 호출되는 콜백함수. 캔들의 period 마다 호출된다.
        """
        self.cb_update_candle = update_candle

    # candle handler 에서 호출해준다.
    def _update_candle(self, df):
        # 캔들업뎃호출
        if self.cb_update_candle:
            self.cb_update_candle(df, df.iloc[-1])

    async def load(self):
        pass

    async def start(self):
        try:
            if self.candle_handler:
                # await
                self.candle_handler.start()
            else:
                logger.info('candle_handler 를 사용하지 않습니다.')
        except:
            utils.print_traceback()
