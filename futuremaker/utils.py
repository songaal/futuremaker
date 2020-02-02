import aiohttp
import asyncio
import os
import sys
import traceback
from collections import defaultdict
from datetime import datetime
import json
from enum import Enum
import time, urllib, hmac, hashlib
from os.path import getmtime

import math

from futuremaker import config
from futuremaker.log import logger


def generate_signature():
    pass

def print_traceback():
    try:
        exc_info = sys.exc_info()
    finally:
        # Display the *original* exception
        traceback.print_exception(*exc_info)
        del exc_info

def json_converter(o):
    if isinstance(o, datetime):
        return o.__str__()
    elif isinstance(o, Enum):
        return o.name


def json_dumps(data):
    return json.dumps(data, default=json_converter)


def parse_param_map(list):
    params = defaultdict(lambda: None, [arg.split('=', maxsplit=1) for arg in list])
    return params


def test_async(coro):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(coro)


def generate_nonce():
    return int(round(time.time() + 3600))


def round_up(val, round_unit):
    val = round(val, 1)
    if val % round_unit == 0:
        return val
    else:
        return val - (val % round_unit) + round_unit


def round_down(val, round_unit):
    val = round(val, 1)
    if val % round_unit == 0:
        return val
    else:
        return val - (val % round_unit)


def floor_int(val, count):
    return math.floor(val / 10**count) * 10**count


def floor(val, count):
    return math.floor(val * 10**count) / 10**count


def correct_price_05(order_qty, price):
    if order_qty > 0:
        order_price = round_up(price, 0.5)
    else:
        order_price = round_down(price, 0.5)
    return order_price


def restart():
    logger.info("Restarting the marketmaker...")
    cmd = [sys.executable] + sys.argv
    logger.info("Restarting cmd >> %s", cmd)
    os.execv(sys.executable, cmd)


def watch_file():
    watched_files_mtimes = [(f, getmtime(f)) for f in config.WATCHED_FILES]
    return watched_files_mtimes


def check_file():
    for f, mtime in watch_file():
        if getmtime(f) > mtime:
            restart()


def XBt_to_XBT(XBt):
    return float(XBt) / 100000000


def period_to_freq(period):
    """
    1m, 4h 등의 period를 pandas 기반의 D, H, T로 바꿔준다.
    [pandas time 기호]
    B	Business day
    D	Calendar day
    W	Weekly
    M	Month end
    Q	Quarter end
    A	Year end
    BA	Business year end
    AS	Year start
    H	Hourly frequency
    T, min	Minutely frequency
    S	Secondly frequency
    L, ms	Millisecond frequency
    U, us	Microsecond frequency
    N, ns	Nanosecond frequency

    :param period:
    :return:
    """
    return period.replace('m', 'T').upper()


def _extract_topic(topic_request):
    list = []
    for str in topic_request['args']:
        tmp = str.split(':')
        list.append(tmp[0])
    return list


async def send_telegram(telegram_bot_token, telegram_chat_id, text):
    if telegram_bot_token and telegram_chat_id:
        # logger.info('Telegram %s [%s] [%s]', text, telegram_chat_id, telegram_bot_token)
        url = f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage'
        data = {
            'chat_id': telegram_chat_id,
            'text': text,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                resp = await response.text()
                return resp


def round_up(num, unit=10):
    return (int(num / unit) + 1) * unit
