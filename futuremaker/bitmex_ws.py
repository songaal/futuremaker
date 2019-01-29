import asyncio
import json
import traceback

import websockets

from futuremaker import utils
from futuremaker.log import logger
from futuremaker.utils import generate_nonce, generate_signature

BITMEX_REAL_URL = 'wss://www.bitmex.com/realtime'
BITMEX_TEST_URL = 'wss://testnet.bitmex.com/realtime'


class BitmexWS(object):

    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_TABLE_LEN = 200

    def __init__(self, symbol, candle_period=None, api_key=None, api_secret=None, testnet=False):
        self.url = BITMEX_TEST_URL if testnet else BITMEX_REAL_URL
        self.api_key = api_key
        self.api_secret = api_secret
        self.connected = False
        self.websocket = None

        private_topic = ['margin',
                         f'order:{symbol}',
                         f'position:{symbol}']
        public_topic = [f'instrument:{symbol}',
                        f'orderBook10:{symbol}']

        if candle_period:
            public_topic.append(f'tradeBin{candle_period}:{symbol}')

        if api_key and api_secret:
            self.topic_request = {'op': 'subscribe', 'args': public_topic + private_topic}
        else:
            self.topic_request = {'op': 'subscribe', 'args': public_topic}

        self.topics = utils._extract_topic(self.topic_request)

        # topic 데이터 저장소.
        self.data = dict()
        self.keys = dict()
        self.is_ready = False

    async def connect(self):
        self.websocket = await websockets.connect(self.url, extra_headers=self.__get_auth())
        self.connected = True
        logger.info('Connected! websocket > %s...', self.websocket)
        if self.websocket:
            text = utils.json_dumps(self.topic_request)
            await self.websocket.send(text)

    async def listen(self):
        if self.websocket:
            while True:
                try:
                    message = await self.websocket.recv()
                    self.__on_message(message)
                except Exception as e:
                    logger.error('listen error', e)
                    self.connected = False
                    logger.error('########################################')
                    logger.error('########################################')
                    logger.error('########################################')
                    logger.error('Websocket closed. %s', e)
                    logger.error('########################################')
                    logger.error('########################################')
                    logger.error('########################################')
                    logger.error('Try websocket reconnect in 5 seconds...')
                    # 5초후 웹소켓 접속 재시도.
                    await asyncio.sleep(5)
                    await self.connect()
        else:
            raise Exception('Websocket disconnected.')

    async def wait_ready(self):
        if not self.is_ready:
            while len(self.data) < len(self.topics):
                await asyncio.sleep(1)

            self.is_ready = True

    def __get_auth(self):
        '''Return auth headers. Will use API Keys if present in settings.'''
        if self.api_key:
            logger.info("BitMEX websocket is authenticated with API Key.")
            # To auth to the WS using an API key, we generate a signature of a nonce and
            # the WS API endpoint.
            expires = generate_nonce()
            return {
                'api-expires': str(expires),
                'api-signature': generate_signature(self.api_secret, 'GET', '/realtime', expires, ''),
                'api-key': self.api_key,
            }
        else:
            logger.warn("BitMEX websocket is not authenticated.")
            return {}

    def __on_message(self, message):
        '''Handler for parsing WS messages.'''
        message = json.loads(message)
        logger.debug(json.dumps(message))

        table = message['table'] if 'table' in message else None
        action = message['action'] if 'action' in message else None
        try:
            if 'subscribe' in message:
                logger.debug("Subscribed to %s." % message['subscribe'])
            elif action:

                if table not in self.data:
                    self.data[table] = []

                # There are four possible actions from the WS:
                # 'partial' - full table image
                # 'insert'  - new row
                # 'update'  - update row
                # 'delete'  - delete row
                value = message['data']
                if action == 'partial':
                    logger.debug("%s: partial" % table)
                    self.data[table] += value
                    # Keys are communicated on partials to let you know how to uniquely identify
                    # an item. We use it for updates.
                    self.keys[table] = message['keys']
                elif action == 'insert':
                    logger.debug('%s: inserting %s' % (table, value))
                    self.data[table] += value

                    # Limit the max length of the table to avoid excessive memory usage.
                    # Don't trim orders because we'll lose valuable state if we do.
                    if table not in ['order', 'orderBookL2'] and len(self.data[table]) > BitmexWS.MAX_TABLE_LEN:
                        self.data[table] = self.data[table][int(BitmexWS.MAX_TABLE_LEN / 2):]

                elif action == 'update':
                    logger.debug('%s: updating %s' % (table, value))
                    # Locate the item in the collection and update it.
                    for updateData in value:
                        item = findItemByKeys(self.keys[table], self.data[table], updateData)
                        if not item:
                            return  # No item found to update. Could happen before push
                        item.update(updateData)
                        # Remove cancelled / filled orders
                        if table == 'order' and item['leavesQty'] <= 0:
                            self.data[table].remove(item)
                elif action == 'delete':
                    logger.debug('%s: deleting %s' % (table, value))
                    # Locate the item in the collection and remove it.
                    for deleteData in value:
                        item = findItemByKeys(self.keys[table], self.data[table], deleteData)
                        self.data[table].remove(item)
                else:
                    raise Exception("Unknown action: %s" % action)

                # 업데이트 콜백을 호출한다.

                for item in value:
                    if self.is_ready:
                        if table.startswith('tradeBin'):
                            if self.update_candle and item:
                                self.update_candle(item)
                        elif table == 'orderBook10':
                            if self.update_orderbook and item:
                                self.update_orderbook(item)
                        elif table == 'order':
                            if self.update_order and item:
                                self.update_order(item)
                    if table == 'position':
                        if self.update_position and item:
                            self.update_position(item)
        except:
            logger.error(traceback.format_exc())

# Utility method for finding an item in the store.
# When an update comes through on the websocket, we need to figure out which item in the array it is
# in order to match that item.
#
# Helpfully, on a data push (or on an HTTP hit to /api/v1/schema), we have a "keys" array. These are the
# fields we can use to uniquely identify an item. Sometimes there is more than one, so we iterate through all
# provided keys.
def findItemByKeys(keys, table, matchData):
    for item in table:
        matched = True
        for key in keys:
            if item[key] != matchData[key]:
                matched = False
        if matched:
            return item