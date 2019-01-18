import asyncio
import os
import time
from datetime import datetime

from aiohttp import web

from futuremaker import utils
from futuremaker.telegram_bot_adapter import TelegramBotAdapter
from futuremaker.bitmex.nexus import Nexus
from futuremaker.log import logger


class Algo(object):
    """
    봇 알고리즘.
    nexus 객체를 가지고 있으며 다음과 같이 사용가능하다.
    nexus.api: 오더, 잔고, 히스토리 api 호출
    nexus['<토픽'>]: 웹소켓으로 업데이트되는 토픽데이터가 담기는 저장소. 값이 필요할때 접근가능하다.
    """

    def __init__(self, symbol, leverage=None, candle_limit=20, candle_period='1m', api_key=None, api_secret=None,
                 testnet=True, dry_run=False, telegram_bot_token=None, telegram_chat_id=None, http_port=None):
        if not symbol:
            raise Exception('Symbol must be set.')
        if not candle_period:
            raise Exception('candle_period must be set. 1m, 5m,..')

        self.symbol = symbol
        self.candle_period = candle_period
        self.http_port = http_port
        self.nexus = Nexus(symbol, leverage=leverage, api_key=api_key, api_secret=api_secret, testnet=testnet,
                           dry_run=dry_run, candle_limit=candle_limit, candle_period=candle_period,
                           update_orderbook=self.update_orderbook, update_candle=self.update_candle,
                           update_order=self.update_order, update_position=self.update_position)
        self.telegram_bot = TelegramBotAdapter(bot_token=telegram_bot_token, chat_id=telegram_chat_id, expire_time=600)

    async def init(self):
        """
        이 부분을 호출하여 넥서스를 초기화한다.
        :return:
        """
        try:
            await self.nexus.wait_ready()
        except Exception as e:
            logger.error('init error > %s', e)
            utils.print_traceback()

    async def schedule(self):
        """
        반복적인 일이 있을때 구현한다.
        :return:
        """
        pass

    def update_orderbook(self, orderbook):
        """
        orderbook이 업데이트되어 들어온다.
        {
            'symbol': 'XBTUSD',
            'timestamp': '2019-01-12T08: 07: 23.150Z',
            'bids': [
                [
                    3609.5,
                    1070
                ],
                ....
            ],
            'asks': [
                [
                    3610,
                    813
                ],
                ....
            ]
        }
        :return:
        """
        pass

    def update_candle(self, df, candle):
        """
        캔들이 업데이트되어 dict가 들어온다.
        :param df: pandas.DataFrame
        :param candle: dict
        :return:
        """
        pass

    def update_order(self, order):
        """
        업데이트된 order 가 들어온다. nexus['order']['<orderID'] 로도 접근가능.
        :param order:
        :return:
        """
        pass

    def update_position(self, position):
        """
        업데이트된 position 이 들어온다. nexus['position'] 으로 접근한 객체와 동일하다.
        :param position:
        :return:
        """
        pass

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            logger.info('SYMBOL: %s', self.symbol)
            logger.info('CANDLE_PERIOD: %s', self.candle_period)
            logger.info('NOW: %s', datetime.now())
            logger.info('UCT: %s', datetime.utcnow())
            logger.info('ENV[TZ]: %s', os.getenv("TZ"))
            logger.info('LOGLEVEL: %s', os.getenv("LOGLEVEL"))
            logger.info('TZNAME: %s', time.tzname)
            logger.info('Loading...')
            nexus_load = loop.create_task(self.nexus.load())
            loop.run_until_complete(self.init())
            scheduled_task = loop.create_task(self.schedule())
            if self.http_port:
                server_task = loop.create_task(self._run_server())
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.stop()

    async def _run_server(self):
        try:
            app = web.Application()
            app.add_routes([
                web.get('/', self._handle_info),
            ])
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', self.http_port)
            await site.start()
            logger.info('HTTP server bind port %s', self.http_port)
        except Exception as e:
            logger.error('_run_server error %s', e)

    async def _handle_info(self, request):
        return web.Response(body='{}'.format(self.__class__.__name__))

    async def _post_orders(self):
        pass

    async def _get_orders(self):
        pass
