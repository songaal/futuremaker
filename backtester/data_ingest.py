import csv
import json
import os
import re
import tempfile
import time
import timeit
from datetime import datetime, timedelta

from futuremaker.log import logger


# async def ingest_data(exchange, symbol, start_date, end_date, periods):
#     base_dir = None
#     period_pairs = list(map(lambda x: x.strip(), periods.split(',')))
#     if symbol:
#         for pair in period_pairs:
#             pairs = pair.split(':')
#             interval, history = pairs[0], int(pairs[1])
#             base_dir = await _ingest_one_data(exchange, symbol, start_date, end_date, interval, history)
#
#     return base_dir


async def ingest_data(exchange, symbol, start_date, end_date, interval, history):
    """
    데이터를 받아서 csv파일로 저장한다.
    만약 파일이 존재한다면 스킵한다.
    :return: 해당 파일이 존재하는 디렉토리 경로.
    """
    dir = tempfile.gettempdir()
    timer_start = timeit.default_timer()
    tz = start_date.tzinfo

    # 값, 단위 분리
    interval_num, interval_unit = split_interval(interval)

    interval = interval.lower()
    interval_unit = interval_unit.lower()

    if interval_unit in ['w', 'd', 'h']:
        # 주, 일, 시 단위
        resolution = interval_unit if interval_num == '1' else interval
    elif interval_unit in ['m']:
        # 분 단위
        resolution = interval_num

    base_dir, filepath = ingest_filepath(dir, exchange, symbol, start_date, end_date, interval, history)

    logger.debug('file_path=%s', filepath)
    if os.path.exists(filepath):
        logger.debug('# [{}] CandleFile Download Passed. {}'.format(symbol, filepath))
        return base_dir, filepath

    prepare_date = get_prepare_date(start_date, interval, history)
    since = int(prepare_date.timestamp()) * 1000
    logger.debug('Ingest time range: %s ~ %s', prepare_date, end_date)

    ##FIXME
    limit = 750

    candles = await fetch_ohlcv(exchange, symbol, interval, since, limit)

    logger.debug('#### fetch_ohlcv response [%s] >> \n%s', len(candles), candles)

    f = open(filepath, 'w', encoding='utf-8', newline='')
    wr = csv.writer(f)

    if len(candles) == 0:
        raise ValueError('[FAIL] candle data row 0')

    wr.writerow(['Datetime', 'Index', 'Open', 'High', 'Low', 'Close', 'Volume'])
    for candle in candles:
        wr.writerow([
            datetime.fromtimestamp(int(candle[0]/1000), tz=tz).strftime('%Y-%m-%d %H:%M:%S'),
            int(candle[0]),
            '{:.8f}'.format(candle[1]),
            '{:.8f}'.format(candle[2]),
            '{:.8f}'.format(candle[3]),
            '{:.8f}'.format(candle[4]),
            '{:.2f}'.format(candle[5]),
        ])

    timer_end = timeit.default_timer()
    logger.debug('# {} Downloaded CandleFile. elapsed: {}'.format(symbol, str(timer_end - timer_start)))
    return base_dir, filepath


async def fetch_ohlcv(exchange, symbol, interval, since, limit):
    if exchange.has['fetchOHLCV']:
        if symbol in exchange.markets_by_id:
            market = exchange.markets_by_id[symbol]
            symbol = market['symbol']
            time.sleep(exchange.rateLimit / 1000)  # time.sleep wants seconds
            return await exchange.fetch_ohlcv(symbol, timeframe=interval, since=since, limit=limit)


def split_interval(time_interval):
    """
    2h, 1d, 30m 과 같이 입력된 인터벌을 분리한다.
    :param time_interval:
    :return:
    """
    unit = None
    number = int(re.findall('\d+', time_interval)[0])
    maybeAlpha = time_interval[-1]
    if maybeAlpha.isalpha():
        unit = maybeAlpha.lower()
    return number, unit


def get_prepare_date(start_date, interval, history):
    """
    start_date 에서 interval 을 history 갯수만큼 뺀 날짜를 찾는다. 데이터를 가져오기 위한 시작날짜.
    :param start_date:
    :param interval:
    :param history:
    :return:
    """
    number, unit = split_interval(interval)
    # 자신을 포함하므로 1개이면 n이 0 이 된다. 즉, history -1 만큼을 추가해준다.
    n = (history - 1) * number
    diff = None
    if unit == 'd':
        diff = timedelta(days=n)
    elif unit == 'h':
        diff = timedelta(hours=n)
    elif unit == 'm':
        diff = timedelta(minutes=n)

    prepare_date = start_date - diff
    return prepare_date


def ingest_filename(symbol, period, history):
    return '{}_{}_{}.csv'.format(symbol.replace('/', '_').lower(), period, history)


def ingest_filepath(root_dir, exchange, symbol, start_date, end_date, period, history):
    filename = ingest_filename(symbol, period, history)
    base_dir = '{}/{}/{}-{}'.format(root_dir,
                                     exchange.id,
                                     start_date.strftime('%Y%m%d%H%M%Z'),
                                     end_date.strftime('%Y%m%d%H%M%Z')
                                     )
    try:
        os.makedirs(base_dir, exist_ok=True)
    except OSError as e:
        raise e

    return base_dir, os.path.join(base_dir, filename)

