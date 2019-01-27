import csv
import os
import re
import tempfile
import time
import timeit
from datetime import datetime, timedelta

from futuremaker.log import logger


async def ingest_data(api, symbol, start_date, end_date, interval, history=0, reload=False):
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

    base_dir, filepath = ingest_filepath(dir, api, symbol, start_date, end_date, interval, history)

    logger.debug('file_path=%s', filepath)
    # 강제 리로드 요청이 없고, 파일이 존재하고, 사이즈도 0보다 크면, 그냥 사용.
    if not reload and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        logger.debug('# [{}] CandleFile Download Passed. {}'.format(symbol, filepath))
        return base_dir, filepath

    prepare_date = get_prepare_date(start_date, interval, history)
    delta = (end_date - prepare_date)
    # 나누어 받을때 다음번 루프의 시작시점이 된다.
    next_delta = 0
    if interval_unit == 'm':
        length = (delta.days * 24 * 60 + delta.seconds // 60) // interval_num
        next_delta = timedelta(minutes=interval_num).total_seconds()
    elif interval_unit == 'h':
        length = (delta.days * 24 + delta.seconds // 3600) // interval_num
        next_delta = timedelta(hours=interval_num).total_seconds()
    elif interval_unit == 'd':
        length = (delta.days) // interval_num
        next_delta = timedelta(days=interval_num).total_seconds()

    since = int(prepare_date.timestamp()) * 1000
    logger.info('Ingest time range: %s ~ %s', prepare_date, end_date)
    logger.info('Ingest candle length[%s] of [%s] since[%s]', length, interval_unit, since)

    params = {}
    if api.id == 'bitmex':
        max_limit = 750
        # params = { 'partial': 'true' }
    elif api.id == 'binance':
        max_limit = 1000

    with open(filepath, 'w', encoding='utf-8', newline='') as f:

        wr = csv.writer(f)
        wr.writerow(['Datetime', 'Index', 'Open', 'High', 'Low', 'Close', 'Volume'])

        seq = 0
        while length > 0:
            if seq > 0:
                time.sleep(api.rateLimit / 1000)  # time.sleep wants seconds

            limit = min(length, max_limit)
            logger.debug('#### fetch_ohlcv request [%s / %s]', limit, length)
            candles = await fetch_ohlcv(api, symbol, interval, since, limit, params)
            # 읽은 갯수만큼 빼준다.
            length -= limit
            logger.debug('#### fetch_ohlcv remnant [%s]', length)
            logger.debug('#### fetch_ohlcv response [%s] >> \n%s', len(candles), candles)

            if len(candles) == 0:
                logger.warn('candle data rows are empty!')
                break

            last_candle = None
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
                last_candle = candle

            # 다음번 루프는 마지막 캔들부터 이어서 내려받는다.
            logger.debug('>>> last_candle >>> %s', last_candle)
            since = last_candle[0] + next_delta
            seq += 1

    timer_end = timeit.default_timer()
    logger.debug('# {} Downloaded CandleFile. elapsed: {}'.format(symbol, str(timer_end - timer_start)))
    return base_dir, filepath


async def fetch_ohlcv(api, symbol, interval, since, limit, params=None):
    if api.has['fetchOHLCV']:
        if symbol in api.markets:
            return await api.fetch_ohlcv(symbol, timeframe=interval, since=since, limit=limit, params=params)


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
                                     start_date.strftime('%Y%m%d%H%M%z'),
                                     end_date.strftime('%Y%m%d%H%M%z')
                                     )
    try:
        os.makedirs(base_dir, exist_ok=True)
    except OSError as e:
        raise e

    return base_dir, os.path.join(base_dir, filename)

