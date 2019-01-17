import os
import sys

from futuremaker import indicators, utils
from futuremaker.Telegram_bot_adapter import TelegramBotAdapter
from futuremaker.bitmex.algo import Algo
from futuremaker.log import logger
import talib as ta

VERSION='1.0.0'


class AlertGo(Algo):

    def __init__(self, params):
        symbol = params['symbol']
        candle_period = params['candle_period']
        http_port = params['http_port']
        leverage = 1
        candle_limit = 20
        api_key = os.getenv('API_KEY')
        api_secret = os.getenv('API_SECRET')
        telegram_bot_token =os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        testnet = os.getenv('TESTNET') == 'True'
        dry_run = os.getenv('DRY_RUN') == 'True'
        super(AlertGo, self).__init__(symbol=symbol, leverage=leverage, candle_limit=candle_limit,
                                      candle_period=candle_period, api_key=api_key, api_secret=api_secret,
                                      testnet=testnet, dry_run=dry_run, telegram_bot_token=telegram_bot_token,
                                      telegram_chat_id=telegram_chat_id, http_port=http_port)

        self.telegram_bot = TelegramBotAdapter(bot_token=telegram_bot_token, chat_id=telegram_chat_id,
                                               expire_time=600)

    def update_orderbook(self, orderbook):
        pass

    def update_candle(self, df, candle):
        logger.info('update_candle %s > %s : %s', df.index[-1], df.iloc[-1], candle)
        price = df.Close[-1]
        m, u, l = indicators.bollinger_bands(df.Close, n=20, stdev=1.5)

        high = round(u[-1], 2)
        low = round(l[-1], 2)
        logger.info('BBands high[%s] price[%s] low[%s]', high, price, low)
        df = indicators.RSI(df, period=14)
        rsi2 = ta.RSI(df.Close.values)
        rsi = df.RSI[-1]
        rsi = round(rsi, 2)
        rsi2 = round(rsi2[-1], 2)
        logger.info('RSI[%s] RSI2[%s]', rsi, rsi2)

        score = 0
        if price >= high:
            logger.info('BBands Upper touched! price[%s] >= bbhigh[%s]', price, high)
            score += 1
        elif price <= low:
            logger.info('BBands Lower touched! price[%s] <= bblow[%s]', price, low)
            score -= 1

        if rsi >= 60:
            logger.info('RSI[%s] >= 60.', rsi)
            score += 1
        elif rsi <= 40:
            logger.info('RSI[%s] <= 40.', rsi)
            score -= 1

        order_qty = 10
        if score >= 2:
            text = f'주문타입: <b>BUY</b>\n' \
                   f'가격: {df.Close[-1]}\n' \
                   f'수량: {order_qty}\n' \
                   f'이유: {self.symbol} Too much buy! price[{price}] >= bbhigh[{high}] AND RSI[{rsi}] >= 60\n'
            self.telegram_bot.send_question(question_text=text,
                                            yes_name="BUY",
                                            yes_func=self.order,
                                            yes_param={"df": df, "qty": order_qty},
                                            no_name="CANCEL")
        elif score <= -2:
            text = f'주문타입: <b>SELL</b>\n' \
                   f'가격: {df.Close[-1]}\n' \
                   f'수량: {-order_qty}\n' \
                   f'이유: {self.symbol} Too much sell! price[{price}] <= bblow[{low}] AND RSI[{rsi}] <= 40\n'
            self.telegram_bot.send_question(question_text=text,
                                            yes_name="SELL",
                                            yes_func=self.order,
                                            yes_param={"df": df, "qty": -order_qty},
                                            no_name="CANCEL")

    def update_order(self, order):
        logger.info('update_order > %s', order)

    def update_position(self, position):
        logger.info('update_position > %s', position)

    def order(self, param):
        stop_limit_order = self.nexus.api.put_order(order_qty=param['df'].Close[-1],
                                                    price=param['df'].Close[-1],
                                                    stop_price=param['df'].Close[-1],
                                                    type="Limit")
        logger.info("주문결과: %s", stop_limit_order)
        return stop_limit_order["ordStatus"]


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    bot = AlertGo(params)
    bot.run()
