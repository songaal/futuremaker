from futuremaker import utils
from futuremaker.exception import OrderNotFoundException
from futuremaker.log import logger, order_logger


class BitmexAPI(object):
    """
    REST API 주문실행모듈
    """

    def __init__(self, client, symbol, dry_run=True):
        """
        :param client:
        :param symbol:
        :param leverage:
        :param dry_run: 참일 경우 실제 주문을 보내지 않음.
        """
        self.client = client
        self.symbol = symbol
        self.dry_run = dry_run
        self.leverage = None

    def update_leverage(self, leverage):
        # update leverage
        self.leverage = leverage
        if not self.dry_run:
            result = self.client.Position.Position_updateLeverage(symbol=self.symbol, leverage=leverage).result()
            logger.debug('UPDATE LEVERAGE symbol[%s] leverage[%s] Result > %s', self.symbol, self.leverage, result[0])

    def put_order(self, order_qty, price=None, stop_price=None, post_only=True, close_position=True, type='Limit'):
        order_logger.info('NEW ORDER > symbol[%s] type[%s] order_qty[%s] price[%s] stop_price[%s]',
                          self.symbol, type, order_qty, price, stop_price)
        if self.dry_run:
            return

        try:
            if type == 'Limit':
                result = self.client.Order.Order_new(symbol=self.symbol, ordType=type, orderQty=order_qty,
                                                     price=price,
                                                     side='Buy' if order_qty > 0 else 'Sell',
                                                     execInst='ParticipateDoNotInitiate' if post_only else '').result()
            elif type == 'Stop':
                if close_position:
                    result = self.client.Order.Order_new(symbol=self.symbol, ordType=type, stopPx=stop_price,
                                                         execInst='Close,LastPrice',
                                                         side='Buy' if order_qty > 0 else 'Sell').result()
                else:
                    result = self.client.Order.Order_new(symbol=self.symbol, ordType=type,
                                                         orderQty=order_qty, stopPx=stop_price).result()

            elif type == 'LimitIfTouched' or type == "StopLimit":
                result = self.client.Order.Order_new(symbol=self.symbol, ordType=type, orderQty=order_qty,
                                                     price=price, stopPx=stop_price,
                                                     execInst='ParticipateDoNotInitiate').result()
            elif type == 'Market':
                result = self.client.Order.Order_new(symbol=self.symbol, ordType=type, orderQty=order_qty,
                                                     price=price).result()

            logger.debug('NEW ORDER > symbol[%s] Result > %s', self.symbol, result[0])
            order = result[0]
            status = order['ordStatus']
            if status != 'Rejected':
                return order
        except Exception as e:
            logger.error('put order error %s', e)

    def amend_order(self, order, order_qty, price=None, stop_price=None, type='Limit'):
        """
        기존 주문 수정.
        :param key:
        :param order_qty:
        :param price:
        :return:
        """
        if not self.dry_run:
            try:
                order_id = order['orderID']

                if type == 'Limit':
                    result = self.client.Order.Order_amend(orderID=order_id, orderQty=order_qty,
                                                           price=price).result()
                elif type == 'Stop':
                    result = self.client.Order.Order_amend(orderID=order_id, orderQty=order_qty,
                                                           stopPx=stop_price).result()
                elif type == 'LimitIfTouched' or type == "StopLimit":
                    result = self.client.Order.Order_amend(orderID=order_id, orderQty=order_qty,
                                                           price=price, stopPx=stop_price).result()
                elif type == 'Market':
                    result = self.client.Order.Order_new(symbol=self.symbol, ordType=type, orderQty=order_qty,
                                                         price=price).result()
                logger.debug('AMEND ORDER > order_id[%s] symbol[%s] Result > %s', order_id, self.symbol, result[0])
                order = result[0]
                status = order['ordStatus']

                order_logger.info(
                    'AMEND ORDER (%s) > order_id[%s] symbol[%s] type[%s] order_qty[%s] price[%s] stop_price[%s]',
                    status, order_id, self.symbol, type, order_qty, price, stop_price)

                if status != 'Rejected':
                    return order

            except Exception as e:
                if 'Invalid ordStatus' in e.response.text:
                    raise OrderNotFoundException()
                logger.error('amend order error %s', e)

    def cancel_order(self, order):
        order_id = order['orderID']
        if not self.dry_run:
            result = self.client.Order.Order_cancel(orderID=order_id).result()
            logger.debug('CANCEL ORDER > order_id[%s] symbol[%s] Result > %s', order_id, self.symbol, result[0])

    def fetch_candles(self, period, limit, reverse=False):
        """
        [
          {
            "timestamp": "2019-01-04T08:58:00.000Z",
            "symbol": "XBTUSD",
            "open": 3799.5,
            "high": 3799,
            "low": 3799,
            "close": 3799,
            "trades": 7,
            "volume": 300,
            "vwap": 3799,
            "lastSize": 83,
            "turnover": 7896900,
            "homeNotional": 0.07896900000000001,
            "foreignNotional": 300
          },
          {
            "timestamp": "2019-01-04T08:57:00.000Z",
        ]
        """
        result = self.client.Trade.Trade_getBucketed(symbol=self.symbol, reverse=reverse, count=limit, binSize=period).result()
        return result[0]

    def order_history(self, count=100, reverse=True, status='Filled'):
        if status:
            filter = {
                'ordStatus': status
            }
            filter_json = utils.json_dumps(filter)
        result = self.client.Execution.Execution_getTradeHistory(symbol=self.symbol, count=count, reverse=reverse,
                                                                 filter=filter_json,
                                                                 columns='side,lastQty,orderQty,price,ordType,ordStatus,commission,text,execComm'
                                                                 ).result()
        return result[0]

    def wallet(self, count=100):
        result = self.client.User.User_getWalletHistory(currency='XBt', count=count).result()
        return result[0]

    def get_order(self, count=100):
        filter = utils.json_dumps({"open": True})
        result = self.client.Order.Order_getOrders(symbol=self.symbol, count=count, filter=filter,
                                                   columns="orderID,symbol,side,simpleOrderQty," +
                                                           "orderQty,price,stopPx,ordType,ordStatus," +
                                                           "leavesQty,text,timestamp,transactTime").result()[0]
        return result
