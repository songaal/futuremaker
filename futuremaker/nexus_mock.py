import pandas as pd

from futuremaker import utils, data_ingest
from futuremaker.log import logger


class Nexus(object):

    def __init__(self, exchange, symbol, leverage, candle_limit, candle_period, test_start, test_end):
        self.candle_handler = None
        self.symbol = symbol
        self.leverage = leverage
        self.api = utils.ccxt_exchange(exchange, async=True)

        self.candle_limit = candle_limit
        self.candle_period = candle_period
        self.test_start = test_start
        self.test_end = test_end

    def callback(self, update_candle=None, **kwargs):
        """
        데이터 변경시 호출되는 콜백함수들을 설정한다.
        """
        self.cb_update_candle = update_candle

    def _update_candle(self):
        candle_df = self.candle_handler.update()
        # 캔들업뎃호출
        if self.cb_update_candle and candle_df is not None:
            self.cb_update_candle(candle_df, candle_df.iloc[-1])
            return candle_df

    async def start(self):
        if not self.candle_handler:
            logger.error('Nexus mock is not loaded yet!')
            return

        logger.info('Backtest start timer!')
        while True:
            df = self._update_candle()
            if df is None:
                break

    async def load(self):
        try:
            await self.api.load_markets()

            _, filepath = await data_ingest.ingest_data(self.api, self.symbol, self.test_start, self.test_end,
                                                        self.candle_period, self.candle_limit, reload=True)
            self.candle_handler = CandleHandler(filepath, self.candle_limit)
            self.candle_handler.load()
        except:
            utils.print_traceback()

    async def wait_ready(self):
        pass

    def __getitem__(self, item):
        return None


class CandleHandler(object):

    def __init__(self, filepath, history):
        self.filepath = filepath
        self.history = history
        self._data = None
        self._seq = 0
        self._size = 0

    def load(self):
        self._data = pd.read_csv(self.filepath, index_col='Index',
                                 usecols=['Index', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self._size = len(self._data.index)

    def update(self):
        if self._seq + self.history <= self._size:
            df = self._data.iloc[self._seq:self._seq + self.history]
            self._seq += 1
            return df
