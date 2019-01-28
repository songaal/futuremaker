import pandas as pd

from futuremaker.log import logger


class BarList:
    def __init__(self, symbol, history, freq='T'):
        self.symbol = symbol
        self.freq = freq
        self.history = history
        self.df = None

    def init(self, index_list, data_list):
        logger.debug('>> index_list >> %s', index_list)
        # dates = pd.DatetimeIndex(index_list, dtype='datetime64[ns]', freq=self.freq)
        self.df = pd.DataFrame(data=data_list, index=index_list, columns=['Open', 'High', 'Low', 'Close', 'Volume'])

    def update(self, timestamp, open, high, low, close, volume):

        self.df.loc[timestamp] = [open, high, low, close, volume]

        size = len(self.df.index)
        if size > self.history:
            start = size - self.history
            self.df = self.df.iloc[start:]

    def last_datetime(self):
        if len(self.datetime) > 0:
            return self.datetime[-1]
        else:
            return None

    def last_timestamp(self):
        if len(self.df) > 0:
            return self.df.index[-1]
        else:
            return 0

    def size(self):
        return len(self.datetime)

    def is_filled(self):
        return len(self.datetime) >= self.history

    def __str__(self):
        format_str = "BarList: symbol=%s, freq=%s, history=%s, size=%s" % (
                         self.symbol, self.freq, self.history, len(self.df.index)
                        )
        return format_str
