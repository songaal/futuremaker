import os
import sys
from bfxapi import Client, Order

bfx = Client(
    API_KEY='<YOUR_API_KEY>',
    API_SECRET='<YOUR_API_SECRET>'
)

@bfx.ws.on('authenticated')
async def submit_order(auth_message):
    await bfx.ws.submit_order('tBTCUSD', 19000, 0.01, Order.Type.EXCHANGE_MARKET)

bfx.ws.run()