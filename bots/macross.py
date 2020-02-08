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
                         init_capital=init_capital, max_budget=max_budget, commission_rate=commission_rate,
                         buy_unit=0.01, buy_delay=1)

    def ready(self):
        self.wallet_summary()

    def update_candle(self, df, candle, localtime):
        # 양봉이면 사고, 음봉이면 판다.
        sma_short = df.close.rolling(5).mean()[-1]
        sma_long = df.close.rolling(10).mean()[-1]
        diff = sma_short - sma_long

        explain = f'{localtime} close[{candle.close:0.3f}] sma_short [{sma_short:0.3f}] sma_long[{sma_long:0.3f}]'
        if not self.backtest:
            log.logger.info(explain)
            self.send_message(explain)

        if diff > 0:
            if self.position_quantity < 0:
                # close
                quantity = self.close_short()
                self.calc_close(localtime, candle.close, self.position_entry_price, quantity)

            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Long <-- {localtime}')
                self.open_long()
                self.calc_open(Type.LONG, localtime, candle.close, 0)
        elif diff < 0:
            if self.position_quantity > 0:
                #close
                quantity = self.close_long()
                self.calc_close(localtime, candle.close, self.position_entry_price, quantity)

            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Short <-- {localtime}')
                self.open_short()
                self.calc_open(Type.SHORT, localtime, candle.close, 0)


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

    # asyncio.run(test_bot.run(algo))
    asyncio.run(real_bot.run(algo))



