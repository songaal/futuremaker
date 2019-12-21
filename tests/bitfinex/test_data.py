import os
import sys
import asyncio
import time

import pandas as pd

sys.path.append('../')

from bfxapi import Client

bfx = Client(
    logLevel='DEBUG',
)
day = 90
now = int(round(time.time() * 1000))
then = now - (1000 * 60 * 60 * 24 * day) # 10 days ago

async def log_historical_candles():
    candles = await bfx.rest.get_public_candles('tBTCUSD', then, now, tf='1D', sort=-1)
    candles.reverse()
    df = pd.DataFrame(candles, columns=['MTS', 'Open', 'Close', 'High', 'Low', 'Volume'])
    print(df)
    df.to_csv("90d.csv", mode='w')
    print ("Candles:")
    [ print (c) for c in candles ]

async def run():
    try:
        await log_historical_candles()
    except Exception as e:
        print(e)

t = asyncio.ensure_future(run())
asyncio.get_event_loop().run_until_complete(t)