import os
import sys
import asyncio
import time
sys.path.append('../')

from bfxapi import Client, Order

API_KEY=os.getenv("BFX_KEY")
API_SECRET=os.getenv("BFX_SECRET")

bfx = Client(
    API_KEY=API_KEY,
    API_SECRET=API_SECRET,
    logLevel='DEBUG'
)


async def create_order():
    """
    주문 타입.
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'
    STOP = 'STOP'
    STOP_LIMIT = 'STOP LIMIT'
    TRAILING_STOP = 'TRAILING STOP'
    FILL_OR_KILL = 'FOK'
    EXCHANGE_MARKET = 'EXCHANGE MARKET'
    EXCHANGE_LIMIT = 'EXCHANGE LIMIT'
    EXCHANGE_STOP = 'EXCHANGE STOP'
    EXCHANGE_STOP_LIMIT = 'EXCHANGE STOP LIMIT'
    EXCHANGE_TRAILING_STOP = 'EXCHANGE TRAILING STOP'
    EXCHANGE_FILL_OR_KILL = 'EXCHANGE FOK'
    """
    response = await bfx.rest.submit_order("tBTCUSD", 10, 0.1, market_type=Order.Type.LIMIT)
    # response is in the form of a Notification object
    for o in response.notify_info:
        # each item is in the form of an Order object
        print("Order: ", o)

async def cancel_order():
    response = await bfx.rest.submit_cancel_order(36142184891)
    # response is in the form of a Notification object
    # notify_info is in the form of an order object
    print ("Order: ", response.notify_info)

async def update_order():
    response = await bfx.rest.submit_update_order(1185510771, price=15, amount=0.055)
    # response is in the form of a Notification object
    # notify_info is in the form of an order object
    print ("Order: ", response.notify_info)

async def run():
    await create_order()
    await cancel_order()
    await update_order()

t = asyncio.ensure_future(run())
asyncio.get_event_loop().run_until_complete(t)