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
        roc = df['roc']

        # buy_entry = kamaEntry[-1] > kamaEntry[-2] and roc[-2] < 0 and roc[-1] > 0
        # sell_entry = kamaEntry[-1] < kamaEntry[-2] and roc[-2] < 0 and roc[-1] < 0
        # buy_exit = kamaEntry[-1] < kamaEntry[-2] or (roc[-2] > 0 and roc[-1] < 0)
        # sell_exit = kamaEntry[-1] > kamaEntry[-2] or (roc[-2] < 0 and roc[-1] > 0)

        buy_entry = roc[-2] < 0 and roc[-1] > 0
        sell_entry = roc[-2] < 0 and roc[-1] < 0
        buy_exit = (roc[-2] > 0 and roc[-1] < 0)
        sell_exit = (roc[-2] < 0 and roc[-1] > 0)

        # b = tostring(kamaEntry[0]) + ':' + tostring(kamaEntry[1]) + ":" + tostring(roc[0]) + ":" + tostring(roc[1])
        explain = f'{time} {candle.close:0.3f}/{kamaEntry[-1]:0.3f}:{kamaEntry[-2]:0.3f}:{roc[-1]:0.3f}:{roc[-2]:0.3f}'
        if buy_entry:
            # buy_entry
            if self.position_quantity < 0:
                log.logger.info(f'--> Close Short <-- {time}')
                quantity = self.close_short()
                self.calc_close(time, candle.close, self.position_entry_price, -quantity)
            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Long <-- {time}')
                self.open_long()
                print(explain)
                self.calc_open(Type.LONG, time, candle.close, 0)
        elif buy_exit and self.position_quantity > 0:
            # close long
            log.logger.info(f'--> Exit Long <-- {time}')
            quantity = self.close_long()
            self.calc_close(time, candle.close, self.position_entry_price, quantity)

        if sell_entry:
            # sell_entry
            if self.position_quantity > 0:
                log.logger.info(f'--> Close Long <-- {time}')
                quantity = self.close_long()
                self.calc_close(time, candle.close, self.position_entry_price, quantity)
            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Short <-- {time}')
                self.open_short()
                print(explain)
                self.calc_open(Type.SHORT, time, candle.close, 0)
        elif sell_exit and self.position_quantity < 0:
            # close sell
            log.logger.info(f'--> Exit Short <-- {time}')
            quantity = self.close_short()
            self.calc_close(time, candle.close, self.position_entry_price, -quantity)


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    year = 2020
    test_bot = Bot(None, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
                   candle_period='1h',
                   test_start=f'{year}-01-01', test_end=f'{year}-12-31',
                   # test_data='../candle_data/BINANCE_BNBUSDT, 240.csv',
                    test_data='../candle_data/BITFINEX_BTCUSD, 240.csv',
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
# 수수료 0.1 포함. BINANCE_BTCUSDT 4h
# roc 2020 BINANCE
TOT_EQUITY:11195 TOT_PROFIT:1195 (11.95%) DD:4.9% MDD:10.5% TOT_TRADE:40 WIN%:32.5% P/L:3.0
# roc 2020 BITFINEX
TOT_EQUITY:10693 TOT_PROFIT:693 (6.93%) DD:3.3% MDD:10.0% TOT_TRADE:39 WIN%:30.8% P/L:2.8
# roc 2019 BINANCE
TOT_EQUITY:52868 TOT_PROFIT:42868 (428.68%) DD:0.5% MDD:15.3% TOT_TRADE:412 WIN%:36.7% P/L:2.8
# roc 2019 BITFINEX
TOT_EQUITY:41254 TOT_PROFIT:31254 (312.54%) DD:2.1% MDD:16.2% TOT_TRADE:403 WIN%:35.5% P/L:2.7
# roc 2018 BINANCE
TOT_EQUITY:34727 TOT_PROFIT:24727 (247.27%) DD:18.0% MDD:31.2% TOT_TRADE:365 WIN%:41.6% P/L:1.9
# roc 2018 BITFINEX
TOT_EQUITY:29810 TOT_PROFIT:19810 (198.10%) DD:18.3% MDD:30.5% TOT_TRADE:371 WIN%:39.6% P/L:1.9
# roc 2017 BITFINEX
TOT_EQUITY:177185 TOT_PROFIT:167185 (1671.85%) DD:0.1% MDD:21.4% TOT_TRADE:333 WIN%:46.5% P/L:2.3
# roc 2016 BITFINEX
TOT_EQUITY:40155 TOT_PROFIT:30155 (301.55%) DD:4.8% MDD:14.4% TOT_TRADE:384 WIN%:42.7% P/L:2.6
# roc 2015 BITFINEX
TOT_EQUITY:42478 TOT_PROFIT:32478 (324.78%) DD:4.2% MDD:16.6% TOT_TRADE:338 WIN%:37.0% P/L:3.5


---------------
# kama 2019 
TOT_EQUITY:22897 TOT_PROFIT:12897 (128.97%) DD:14.0% MDD:18.9% TOT_TRADE:270 WIN%:34.8% P/L:2.6
"""


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


