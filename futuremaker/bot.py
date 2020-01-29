import asyncio
import os
import time
from datetime import datetime

import requests
from aiohttp import web

from futuremaker import utils
from futuremaker.nexus import Nexus
from futuremaker import nexus_mock
from futuremaker.log import logger


class Bot(object):
    """
    봇.
    nexus 객체를 가지고 있으며 다음과 같이 사용가능하다.
    nexus.api: 오더, 잔고, 히스토리 api 호출
    nexus['<토픽'>]: 웹소켓으로 업데이트되는 토픽데이터가 담기는 저장소. 값이 필요할때 접근가능하다.
    """

    def __init__(self, api, symbol, candle_limit=20, candle_period='1m',
                 testnet=True, dry_run=False, http_port=None,
                 backtest=False, test_start=None, test_end=None, test_data=None):

        if not symbol:
            raise Exception('Symbol must be set.')
        if not candle_period:
            raise Exception('candle_period must be set. 1m, 5m,..')

        # self.exchange = exchange
        self.api = api
        self.symbol = symbol
        self.candle_period = candle_period
        self.http_port = http_port
        self.backtest = backtest
        self.telegram_bot_token = None
        self.telegram_chat_id = None

        if not self.backtest:
            self.nexus = Nexus(api, symbol, testnet=testnet,
                               dry_run=dry_run, candle_limit=candle_limit, candle_period=candle_period)
            # self.telegram = TelegramAdapter(bot_token=telegram_bot_token, chat_id=telegram_chat_id, expire_time=600)
        else:
            self.nexus = nexus_mock.Nexus(api, symbol, candle_limit, test_start, test_end, test_data)

    def send_telegram(self, text):
        if self.telegram_bot_token and self.telegram_chat_id:
            coro = utils.send_telegram(self.telegram_bot_token, self.telegram_chat_id, text)
            asyncio.get_event_loop().create_task(coro)

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
        메시지큐.
        :return:
        """
        pass
        # while True:
        #     try:
        #         text = await self.mqueue.get()
        #         await utils.send_telegram(self.telegram_bot_token, self.telegram_chat_id, text)
        #     except Exception as e:
        #         logger.error('_consume error >> %s', e)

    def run(self, algo):
        self.nexus.callback(update_orderbook=algo.update_orderbook,
                            update_candle=algo.update_candle,
                            update_order=algo.update_order,
                            update_position=algo.update_position)
        # ccxt api 연결.
        algo.api = self.nexus.api
        algo.data = self.nexus.api.data
        algo.send_telegram = self.send_telegram

        loop = asyncio.get_event_loop()
        try:
            logger.info('SYMBOL: %s', self.symbol)
            logger.info('CANDLE_PERIOD: %s', self.candle_period)
            logger.info('NOW: %s', datetime.now())
            logger.info('UCT: %s', datetime.utcnow())
            logger.info('ENV[TZ]: %s', os.getenv("TZ"))
            logger.info('LOGLEVEL: %s', os.getenv("LOGLEVEL"))
            logger.info('TZNAME: %s', time.tzname)
            ip_address = requests.get('https://api.ipify.org?format=json').json()['ip']
            logger.info('IP: %s', ip_address)
            logger.info('Loading...')
            self.send_telegram('Futuremaker Bot started.. {}'.format(ip_address))
            loop.run_until_complete(self.nexus.load())
            nexus_start = loop.create_task(self.nexus.start())
            loop.run_until_complete(self.init())
            scheduled_task = loop.create_task(self.schedule())
            if self.http_port and not self.backtest:
                server_task = loop.create_task(self._run_server())

            async def go():
                await nexus_start
            loop.run_until_complete(go())
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

