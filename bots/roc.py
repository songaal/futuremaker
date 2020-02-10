import asyncio
import sys

from futuremaker import log
from futuremaker import utils, indicators
from futuremaker.algo import Algo
from futuremaker.binance_api import BinanceAPI
from futuremaker.bot import Bot
from futuremaker.position_type import Type


class RocEntry(Algo):
    def __init__(self, base, quote, floor_decimals, init_capital, max_budget,
                 period, paper, buy_unit, buy_delay, commission_rate=0.1):
        super().__init__(base=base, quote=quote, floor_decimals=floor_decimals, init_capital=init_capital,
                         max_budget=max_budget, commission_rate=commission_rate, paper=paper,
                         buy_unit=buy_unit, buy_delay=buy_delay)
        self.period = period

    def ready(self):
        self.wallet_summary()

    def update_candle(self, df, candle, localtime):
        candle = indicators.roc(df, period=self.period)
        roc = df['roc']

        buy_entry = roc[-2] < 0 and roc[-1] > 0
        sell_entry = roc[-2] > 0 and roc[-1] < 0
        buy_exit = (roc[-2] > 0 and roc[-1] < 0)
        sell_exit = (roc[-2] < 0 and roc[-1] > 0)

        explain = f'{localtime} close[{candle.close:0.3f}] roc[{roc[-2]:0.1f}, {roc[-1]:0.1f}]'
        if not self.backtest:
            log.logger.info(explain)
            self.send_message(explain)

        if buy_entry:
            # buy_entry
            if self.position_quantity < 0:
                log.logger.info(f'--> Close Short <-- {localtime}')
                quantity = self.close_short()
                self.calc_close(localtime, candle.close, self.position_entry_price, -quantity)
            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Long <-- {localtime}')
                self.open_long()
                self.calc_open(Type.LONG, localtime, candle.close, 0)
        elif buy_exit and self.position_quantity > 0:
            # close long
            log.logger.info(f'--> Exit Long <-- {localtime}')
            quantity = self.close_long()
            self.calc_close(localtime, candle.close, self.position_entry_price, quantity)

        if sell_entry:
            # sell_entry
            if self.position_quantity > 0:
                log.logger.info(f'--> Close Long <-- {localtime}')
                quantity = self.close_long()
                self.calc_close(localtime, candle.close, self.position_entry_price, quantity)
            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Short <-- {localtime}')
                self.open_short()
                self.calc_open(Type.SHORT, localtime, candle.close, 0)
        elif sell_exit and self.position_quantity < 0:
            # close sell
            log.logger.info(f'--> Exit Short <-- {localtime}')
            quantity = self.close_short()
            self.calc_close(localtime, candle.close, self.position_entry_price, -quantity)


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    year = 2019
    test_bot = Bot(None, symbol='BTCUSDT', candle_limit=10,
                   candle_period='4h',
                   test_start=f'{year}-01-01', test_end=f'{year}-12-31',
                   # test_data='../candle_data/BINANCE_BNBUSDT, 1D.csv',
                   # test_data='../candle_data/BITFINEX_BTCUSD, 240.csv',
                   # test_data='../candle_data/BINANCE_BNBUSDT, 240.csv',
                   # test_data='../candle_data/BINANCE_ETHUSDT, 240.csv',
                   test_data='../candle_data/BITFINEX_BABUSD, 240.csv',
                   # test_data='../candle_data/BINANCE_BTCUSDT, 240.csv'
                   # test_data='../candle_data/BINANCE_ETHUSDT, 240.csv'
                   # test_data='../candle_data/BINANCE_BTCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_BTCUSD, 120.csv'
                   # test_data='../candle_data/BINANCE_ETCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_ETHUSD, 60.csv'
                   )
    real_bot = Bot(BinanceAPI(), symbol='BTCUSDT', candle_limit=10,
                   backtest=False, candle_period='1m')

    algo = RocEntry(base='BTC', quote='USDT', period=12, paper=True, floor_decimals=3,
                    init_capital=1000, max_budget=1000000, buy_unit=0.01, buy_delay=1)

    # asyncio.run(test_bot.run(algo))
    asyncio.run(real_bot.run(algo))
