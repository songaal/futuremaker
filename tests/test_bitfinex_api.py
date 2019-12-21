import os
import sys
from bfxapi import Client, Order
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else: # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

symbol = 'tBTCUSD'
bfx = Client(
    API_KEY=os.getenv('API_KEY'),
    API_SECRET=os.getenv('API_SECRET'),
    logLevel='DEBUG'
)
print('API_KEY: {}'.format(os.getenv('API_KEY')))
print('API_SECRET: {}'.format(os.getenv('API_SECRET')))
print(bfx)


@bfx.ws.on('authenticated')
async def submit_order(auth_message):
    # await bfx.ws.submit_order(symbol, 19000, 0.01, Order.Type.EXCHANGE_MARKET)
    print('Authz: {}'.format(auth_message))


@bfx.ws.on('seed_candle')
async def seed_candle(o):
    print('seed_candle: {}'.format(o))


@bfx.ws.on('new_candle')
async def new_candle(arr):
    print('new_candle: {}'.format(arr))


@bfx.ws.on('connected')
async def start():
    await bfx.ws.subscribe_candles(symbol, '1m')


bfx.ws.run()
