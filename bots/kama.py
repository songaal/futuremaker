import asyncio
import sys

from futuremaker import log
from futuremaker import utils, indicators
from futuremaker.algo import Algo
from futuremaker.binance_api import BinanceAPI
from futuremaker.bot import Bot
from futuremaker.position_type import Type


class KamaEntry(Algo):
    def __init__(self, base='BTC', quote='USDT', floor_decimals=3, init_capital=10000, max_budget=10000):
        super().__init__(base=base, quote=quote, floor_decimals=floor_decimals, init_capital=init_capital, max_budget=max_budget)

    def ready(self):
        self.wallet_summary()

    # 1. 손절하도록. 손절하면 1일후에 집입토록.
    # 2. MDD 측정. 손익비 측정.
    # 3. 자본의 %를 투입.
    def update_candle(self, df, candle):

        candle = indicators.kama(df, period=5)
        # print(candle['kama'], candle['direction'])
        time = candle.name
        self.estimated_profit(time, candle.close)

        # buy_entry =  kamaEntry[0]>kamaEntry[1] and roc[1]<0 and roc[0] >0
        # sell_entry = kamaEntry[0]<kamaEntry[1] and roc[1]<0 and roc[0] <0
        # buy_exit = kamaEntry<kamaEntry[1] or (roc[1]>0 and roc[0]<0)
        # sell_exit =  kamaEntry>kamaEntry[1] or (roc[1]<0 and roc[0]>0)

        kamaEntry = df['kama']
        roc = df['direction']

        buy_entry = kamaEntry[-1] > kamaEntry[-2] and roc[-2] < 0 and roc[-1] > 0
        sell_entry = kamaEntry[-1] < kamaEntry[-2] and roc[-2] < 0 and roc[-1] < 0

        buy_exit = kamaEntry[-1] < kamaEntry[-2] or (roc[-2] > 0 and roc[-1] < 0)
        sell_exit = kamaEntry[-1] > kamaEntry[-2] or (roc[-2] < 0 and roc[-1] > 0)

        if buy_entry and not buy_exit:
            # buy_entry
            if self.position_quantity < 0:
                log.logger.info(f'--> Close Short <-- {time}')
                quantity = self.close_short()
                self.calc_close(time, candle.close, self.position_entry_price, -quantity)
            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Long <-- {time}')
                self.open_long()
                self.calc_open(Type.LONG, time, candle.close, 0)
        elif buy_exit and self.position_quantity > 0:
            # close long
            log.logger.info(f'--> Exit Long <-- {time}')
            quantity = self.close_long()
            self.calc_close(time, candle.close, self.position_entry_price, quantity)

        if sell_entry and not sell_exit:
            # sell_entry
            if self.position_quantity > 0:
                log.logger.info(f'--> Close Long <-- {time}')
                quantity = self.close_long()
                self.calc_close(time, candle.close, self.position_entry_price, quantity)
            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Short <-- {time}')
                self.open_short()
                self.calc_open(Type.SHORT, time, candle.close, 0)
        elif sell_exit and self.position_quantity < 0:
            # close sell
            log.logger.info(f'--> Exit Short <-- {time}')
            quantity = self.close_short()
            self.calc_close(time, candle.close, self.position_entry_price, -quantity)


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    year = 2018
    test_bot = Bot(None, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
                   candle_period='1h',
                   test_start=f'{year}-01-01', test_end=f'{year}-12-31',
                   test_data='../candle_data/BINANCE_BNBUSDT, 240.csv'
                   # test_data='../candle_data/BINANCE_BTCUSDT, 240.csv'
                   # test_data='../candle_data/BINANCE_ETHUSDT, 240.csv'
                   # test_data='../candle_data/BINANCE_BTCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_BTCUSD, 120.csv'
                   # test_data='../candle_data/BINANCE_ETCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_ETHUSD, 60.csv'
                   )
    real_bot = Bot(BinanceAPI(), symbol='BTCUSDT', candle_limit=24 * 7 * 2,
                   backtest=False,
                   candle_period='1m',
                   telegram_bot_token='852670167:AAExawLUJfb-lGKVHQkT5mthCTEOT_BaQrg',
                   telegram_chat_id='352354994'
                   )

    algo = KamaEntry(base='BTC', quote='USDT', floor_decimals=3, init_capital=10000, max_budget=1000000)

    asyncio.run(test_bot.run(algo))
    # asyncio.run(real_bot.run(algo))

"""
# BINANCE_BTCUSDT, 240.csv, 
# 2018, period=4
SUMMARY TOT_EQUITY:22300 TOT_PROFIT:12300 (123.00%) DD:2.6% MDD:20.3% TOT_TRADE:295 WIN%:39.7% P/L:2.0
# 2019, 4
SUMMARY TOT_EQUITY:29418 TOT_PROFIT:19418 (194.18%) DD:7.5% MDD:26.1% TOT_TRADE:306 WIN%:34.6% P/L:2.8
# 2019, 5 
SUMMARY TOT_EQUITY:22913 TOT_PROFIT:12913 (129.13%) DD:14.0% MDD:18.9% TOT_TRADE:270 WIN%:34.8% P/L:2.6

# BINANCE_BNBUSDT, 240.csv, 
# 2019, period=4
SUMMARY TOT_EQUITY:20796 TOT_PROFIT:10796 (107.96%) DD:17.5% MDD:36.2% TOT_TRADE:296 WIN%:38.2% P/L:1.9
# 2018, period=4
SUMMARY TOT_EQUITY:303643 TOT_PROFIT:293643 (2936.43%) DD:3.6% MDD:19.6% TOT_TRADE:278 WIN%:39.9% P/L:2.6
# 2018, 5
SUMMARY TOT_EQUITY:184516 TOT_PROFIT:174516 (1745.16%) DD:5.7% MDD:32.9% TOT_TRADE:265 WIN%:41.1% P/L:2.3
"""


