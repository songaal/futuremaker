import asyncio
import concurrent
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
                 backtest=False, test_start=None, test_end=None, test_data=None,
                 telegram_bot_token=None, telegram_chat_id=None):

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
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

        if not self.backtest:
            self.nexus = Nexus(api, symbol, testnet=testnet,
                               dry_run=dry_run, candle_limit=candle_limit, candle_period=candle_period)
        else:
            self.nexus = nexus_mock.Nexus(api, symbol, candle_limit, test_start, test_end, test_data)

    async def send_telegram(self, text):
        if not self.backtest:
            if self.telegram_bot_token and self.telegram_chat_id:
                return await utils.send_telegram(self.telegram_bot_token, self.telegram_chat_id, text)
            else:
                print('BotToken 과 ChatId 가 설정되어 있지 않아 텔레그램 메시지를 보내지 않습니다.')

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

    async def run(self, algo):
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
            await self.send_telegram(f'{algo.get_name()} Bot started.. {ip_address}')
            logger.info('Loading...')
            await self.nexus.load()
            await self.init()

            scheduled_task = loop.create_task(self.schedule())
            nexus_start = loop.create_task(self.nexus.start())
            await asyncio.gather(scheduled_task, nexus_start)
        except KeyboardInterrupt:
            pass
        finally:
            loop.stop()


