import os
import sys
import datetime

from ccxt import ExchangeError

from futuremaker import indicators, utils
from futuremaker.bitmex.bot import Bot
from futuremaker.log import logger


class AlertGo(Bot):

    def __init__(self, params):
        symbol = 'XBTUSD'
        leverage = 10
        candle_limit = 5
        candle_period = '1m'
        api_key = os.getenv('API_KEY')
        api_secret = os.getenv('API_SECRET')
        testnet = os.getenv('TESTNET') == 'True'
        dry_run = os.getenv('DRY_RUN') == 'True'
        # chat_id = os.getenv('CHAT_ID')
        # telegram_bot_token=None, telegram_chat_id=None, http_port=None
        super(AlertGo, self).__init__(symbol=symbol, leverage=leverage, candle_limit=candle_limit,
                                      candle_period=candle_period, api_key=api_key, api_secret=api_secret,
                                      testnet=testnet, dry_run=dry_run)

        self.count = 0
        self.position = "NTL"
        self.start_time = datetime.datetime.now()
        self.stop_limit_tick = 0.5 * 5
        self.limit_tick = 0.5 * 5
        self.limit_order = None
        self.is_order_request = False
        self.pare_orders = []
        self.order_qty = 10
        self.avg_entry_price = 0

    def update_orderbook(self, orderbook):
        # logger.info('update_orderbook > %s  %s', orderbook['bids'][0], orderbook['asks'][0])
        # for pare_order in self.pare_orders:
        #     print(pare_order)
        pass

    def update_candle(self, df, candle):
        logger.info(f"시장가격: {df.Close[-1]}")
        if self.count < 5:
            self.count += 1
            return
        self.count = 0

        diff_sum = sum(df.Close - df.Open)
        add_qty = 0
        logger.info(f"포지션: {self.position}, 차이가격: {diff_sum}")
        if diff_sum > 0:

            if self.position == "SLD":
                # SLD 포지션이면 정리.
                for pare_order in self.pare_orders:
                    try:
                        self.nexus.api.cancel_order(pare_order["limit_order"])
                    except ExchangeError:
                        logger.debug("<ignore> 없어진 요청.")
                    try:
                        self.nexus.api.cancel_order(pare_order["stop_limit_order"])
                    except ExchangeError:
                        logger.debug("<ignore> 없어진 요청.")

                add_qty = self.limit_order["orderQty"]
                self.limit_order = None
                self.pare_orders = []

            # 매수
            order = self.nexus.api.put_order(order_qty=(self.order_qty + add_qty),
                                             # side="Buy",
                                             price=df.Close[-1] - 0.5
                                             )
            if order["ordStatus"] == "New":
                stop_limit_order = self.nexus.api.put_order(order_qty=-(self.order_qty + add_qty),
                                                            # side="Sell",
                                                            price=df.Close[-1] - 0.5 - self.stop_limit_tick,
                                                            stop_price=df.Close[-1] - 0.5 - self.stop_limit_tick,
                                                            type="StopLimit")
                self.pare_orders.append({
                    "price": df.Close[-1],
                    "position": "BOT",
                    "limit_order": order,
                    "stop_limit_order": stop_limit_order
                })
                self.is_order_request = True

        elif diff_sum < 0:

            if self.position == "BOT":
                # BOT 포지션이면 정리.
                for pare_order in self.pare_orders:
                    try:
                        self.nexus.api.cancel_order(pare_order["limit_order"])
                    except ExchangeError:
                        logger.debug("<ignore> 없어진 요청.")
                    try:
                        self.nexus.api.cancel_order(pare_order["stop_limit_order"])
                    except ExchangeError:
                        logger.debug("<ignore> 없어진 요청.")

                add_qty = self.limit_order["orderQty"]
                self.limit_order = None
                self.pare_orders = []

            # 매도
            order = self.nexus.api.put_order(order_qty=-(self.order_qty + add_qty),
                                             # side="Sell",
                                             price=df.Close[-1] + 0.5)
            if order["ordStatus"] == "New":
                stop_limit_order = self.nexus.api.put_order(order_qty=(self.order_qty + add_qty),
                                                            # side="Buy",
                                                            price=df.Close[-1] + 0.5 + self.stop_limit_tick,
                                                            stop_price=df.Close[-1] + 0.5 + self.stop_limit_tick,
                                                            type="StopLimit")
                self.pare_orders.append({
                    "price": df.Close[-1],
                    "position": "SLD",
                    "limit_order": order,
                    "stop_limit_order": stop_limit_order
                })
                self.is_order_request = True

    def update_order(self, order):
        logger.info('update_order > %s', order)

    def update_position(self, position):
        logger.info('update_position > %s', position)
        try:
            price = position["avgEntryPrice"]
            self.avg_entry_price = position["avgEntryPrice"]
        except KeyError:
            logger.debug("시정 평균가가 변동이 없습니다.")
            price = self.avg_entry_price

        current_qty = 0 if position["currentQty"] is None else position["currentQty"] * -1

        if position['currentQty'] > 0:
            self.position = "BOT"
            price = price + self.limit_tick
        elif position['currentQty'] < 0:
            self.position = "SLD"
            price = price - self.limit_tick
        else:
            self.position = "NTL"

        logger.info(f"규모: {current_qty}, 시장평균가: {price}")
        if position["currentQty"] != 0:
            # 포지션을 가지고 있을 경우
            if self.limit_order is None:
                # 익절 주문.
                self.limit_order = self.nexus.api.put_order(order_qty=current_qty,
                                                            price=price,
                                                            stop_price=price,
                                                            type="LimitIfTouched")

            elif self.limit_order is not None \
                    and self.is_order_request \
                    and self.limit_order["orderQty"] != current_qty:
                # 기존 주문 가격, 규모 수정.
                self.limit_order = self.nexus.api.amend_order(order=self.limit_order,
                                                              order_qty=current_qty,
                                                              price=price,
                                                              stop_price=price,
                                                              type="LimitIfTouched")

            self.is_order_request = False
        else:
            # 포지션이 없을때.
            pass

        if self.count % 2 == 0:
            return

        try:
            last_price = position["lastPrice"]
        except KeyError:
            return

        order_list = self.nexus.api.get_order()
        cancel_orders = []
        remove_orders = []
        for pare_order in self.pare_orders:
            high_price = abs(pare_order["price"]) + (0.5 * 10)
            low_price = abs(pare_order["price"]) - (0.5 * 10)

            # 가격 범위가 넘은 경우
            if last_price > high_price or low_price > last_price:
                cancel_orders.append(pare_order)

            # 대기 중이 아닌경우
            is_deplay = False
            for order in order_list:
                if pare_order["limit_order"]["orderID"] == order["orderID"]:
                    is_deplay = True
                    break
            if not is_deplay:
                remove_orders.append(pare_order)

            # 취소처리
            for cancel_order in cancel_orders:
                remove_orders.append(cancel_order)
                try:
                    self.nexus.api.cancel_order(cancel_order["limit_order"])
                except ExchangeError:
                    pass
                try:
                    self.nexus.api.cancel_order(cancel_order["stop_limit_order"])
                except ExchangeError:
                    pass

            # 저장된 데이터 제거
            for remove_order in remove_orders:
                for pare_order in self.pare_orders:
                    if remove_order["limit_order"]["orderID"] == pare_order["limit_order"]["orderID"]:
                        self.pare_orders.remove(pare_order)
                        break

        # self.nexus.api.order_history()[0]["timestamp"].time() > datetime.datetime.now().time()
        # position["lastPrice"] 시장가
        # position['execQty'] 실행 규모
        # position["currentQty"] 진행중인 포지션 규모
        # position['avgEntryPrice'] 평균진입가격
        # position['markPrice'] 시장평균가
        # position['marginCallPrice'] 청산가
        # position["liquidationPrice"] 청산가.
        # self.nexus.api.order_history()[0]['ordType'] 주문타입


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    bot = AlertGo(params)
    bot.run()
