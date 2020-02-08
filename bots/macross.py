import asyncio
import sys
import time

from futuremaker import log
from futuremaker import utils
from futuremaker.algo import Algo
from futuremaker.binance_api import BinanceAPI
from futuremaker.bot import Bot
from futuremaker.position_type import Type


class MaCrossGo(Algo):
    def __init__(self, base, quote, floor_decimals, paper, init_capital, max_budget, commission_rate):
        super().__init__(base=base, quote=quote, paper=paper, floor_decimals=floor_decimals,
                         init_capital=init_capital, max_budget=max_budget, commission_rate=commission_rate)

    def ready(self):
        self.wallet_summary()

    def update_candle(self, df, candle, localtime):
        candle_time = candle.name
        # 양봉이면 사고, 음봉이면 판다.
        # diff = candle.close - candle.open
        diff = df.close.rolling(5).mean()[-1] - df.close.rolling(10).mean()[-1]
        if diff > 0:
            if self.position_quantity < 0:
                # close
                quantity = self.close_short()
                self.calc_close(candle_time, candle.close, self.position_entry_price, quantity)

            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Long <-- {candle_time}')
                self.open_long()
                self.calc_open(Type.LONG, candle_time, candle.close, 0)
        elif diff < 0:
            if self.position_quantity > 0:
                #close
                quantity = self.close_long()
                self.calc_close(candle_time, candle.close, self.position_entry_price, quantity)

            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Short <-- {candle_time}')
                self.open_short()
                self.calc_open(Type.SHORT, candle_time, candle.close, 0)


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    year = 2019
    test_bot = Bot(None, symbol='BTCUSDT', candle_limit=30,
                   candle_period='1h',
                   test_start=f'{year}-01-01', test_end=f'{year}-12-31',
                   test_data='../candle_data/BINANCE_BTCUSDT, 60.csv',
                   )
    real_bot = Bot(BinanceAPI(), symbol='BTCUSDT', candle_limit=30,
                   backtest=False, candle_period='1m')

    algo = MaCrossGo(base='BTC', quote='USDT', floor_decimals=3, paper=True,
                     init_capital=10000, max_budget=1000000, commission_rate=0.1)

    asyncio.run(test_bot.run(algo))
    # asyncio.run(real_bot.run(algo))



