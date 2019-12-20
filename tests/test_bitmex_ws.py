import unittest

from futuremaker import utils
from futuremaker.bitmex.bitmex_ws import BitmexWS
from futuremaker.log import logger


class TestBitmexWS(unittest.TestCase):
    """
    Tests a simple Signal, Order and Fill cycle for the
    PortfolioHandler. This is, in effect, a sanity check.
    """

    def setUp(self):
        #testnet songaal
        self.api_key = None
        self.api_secret = None

    def test_run(self):
        self.margin = None
        self.orders = dict()
        self.position = None

        def handle_topic(topic, action, data):
            print(topic, action, data)
            if topic == 'margin':
                if action == 'partial':
                    self.margin = data
                elif action == 'update':
                    self.margin.update(data)
                    used_margin = self.margin['maintMargin']
                    avail_margin = self.margin['availableMargin']
                    logger.debug(f'[Margin] used_margin[{used_margin}], avail_margin[{avail_margin}]')

            elif topic == 'order':
                # for order in data:

                if action == 'partial' or action == 'insert':
                    if data:
                        order_id = data['orderID']
                        self.orders[order_id] = data
                else:
                    if data and 'orderID' in data:
                        order_id = data['orderID']
                        working_indicator = data['workingIndicator']
                        if working_indicator:
                            self.orders[order_id].update(data)
                        else:
                            del self.orders[order_id]

                print(self.orders)
                print('--------------------')

            elif topic == 'position':
                if action == 'partial':
                    self.position = data
                else:
                    self.position.update(data)

                # 필수.
                currentQty = self.position['currentQty']
                currency = self.position['currency']
                markPrice = self.position['markPrice']
                timestamp = self.position['timestamp']
                liquidationPrice = self.position['liquidationPrice']

                logger.info('%s %s current_qty[%s]', topic, action, currentQty)

        req = {'op': 'subscribe', 'args': ['tradeBin1m:XBTUSD']}
        ws = BitmexWS('XBTUSD', api_key=self.api_key, api_secret=self.api_secret, testnet=True, )

        async def run():
            logger.debug('ws > %s', ws)
            await ws.connect()

            """
            "affiliate",   // Affiliate status, such as total referred users & payout %
            "execution",   // Individual executions; can be multiple per order
            "order",       // Live updates on your orders
            "margin",      // Updates on your current account balance and margin requirements
            "position",    // Updates on your positions
            "privateNotifications", // Individual notifications - currently not used
            "transact"     // Deposit/Withdrawal updates
            "wallet"       // Bitcoin address balance data, including total deposits & withdrawals
            """
            # req = {'op': 'subscribe', 'args': ['tradeBin1m:XBTUSD', 'order', 'margin', 'position', 'wallet']}
            # req = {'op': 'subscribe', 'args': ['margin', 'position:XBTUSD', 'quote:XBTUSD', 'orderBook10:XBTUSD']}
            # req = {'op': 'subscribe', 'args': ['order:XBTUSD', 'position:XBTUSD', 'wallet']}
            req = {'op': 'subscribe', 'args': ['orderBook10:XBTUSD']}
            ws.update_orderbook = lambda x: print(x)
            await ws.listen()

        utils.test_async(run())

    """
    # position update [{'account': 169818, 'symbol': 'XBTUSD', 'currency': 'XBt', 'currentTimestamp': '2019-01-04T16:27:31.092Z', 'markPrice': 3755.68, 'timestamp': '2019-01-04T16:27:31.092Z', 'lastPrice': 3755.68, 'currentQty': -7, 'liquidationPrice': 1694915}]

    order insert [{'orderID': 'b71bf543-fadf-dd3e-bc61-fb3e44306928', 'clOrdID': '', 'clOrdLinkID': '', 'account': 169818, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 1, 'price': 3779.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': 'ParticipateDoNotInitiate', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 1, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from testnet.bitmex.com', 'transactTime': '2019-01-04T16:27:33.004Z', 'timestamp': '2019-01-04T16:27:33.004Z'}]
    order update [{'orderID': 'b71bf543-fadf-dd3e-bc61-fb3e44306928', 'ordStatus': 'Canceled', 'leavesQty': 0, 'text': 'Canceled: Order had execInst of ParticipateDoNotInitiate\nSubmission from testnet.bitmex.com', 'clOrdID': '', 'account': 169818, 'symbol': 'XBTUSD', 'timestamp': '2019-01-04T16:27:33.004Z'}]
    position update [{'account': 169818, 'symbol': 'XBTUSD', 'currency': 'XBt', 'currentTimestamp': '2019-01-04T16:27:36.091Z', 'markPrice': 3755.42, 'markValue': 186396, 'riskValue': 186396, 'homeNotional': -0.00186396, 'maintMargin': 185989, 'unrealisedGrossPnl': 1967, 'unrealisedPnl': 1967, 'unrealisedPnlPcnt': 0.0107, 'unrealisedRoePcnt': 0.0107, 'timestamp': '2019-01-04T16:27:36.091Z', 'lastPrice': 3755.42, 'lastValue': 186396, 'currentQty': -7, 'liquidationPrice': 1694915}]
    position update [{'account': 169818, 'symbol': 'XBTUSD', 'currency': 'XBt', 'currentTimestamp': '2019-01-04T16:27:41.091Z', 'markPrice': 3755.24, 'markValue': 186403, 'riskValue': 186403, 'homeNotional': -0.00186403, 'maintMargin': 185996, 'unrealisedGrossPnl': 1974, 'unrealisedPnl': 1974, 'timestamp': '2019-01-04T16:27:41.091Z', 'lastPrice': 3755.24, 'lastValue': 186403, 'currentQty': -7, 'liquidationPrice': 1694915}]

    order insert [{'orderID': '4f364691-49a2-757f-babb-f068b2b25652', 'clOrdID': '', 'clOrdLinkID': '', 'account': 169818, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 1, 'price': 3779.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 1, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from testnet.bitmex.com', 'transactTime': '2019-01-04T16:29:44.807Z', 'timestamp': '2019-01-04T16:29:44.807Z'}]
    position update [{'account': 169818, 'symbol': 'XBTUSD', 'currency': 'XBt', 'openOrderBuyQty': 1, 'openOrderBuyCost': -26459, 'timestamp': '2019-01-04T16:29:44.807Z', 'currentQty': -7, 'markPrice': 3755.63, 'liquidationPrice': 1694915}]
    order update [{'orderID': '4f364691-49a2-757f-babb-f068b2b25652', 'workingIndicator': True, 'clOrdID': '', 'account': 169818, 'symbol': 'XBTUSD', 'timestamp': '2019-01-04T16:29:44.807Z'}]
    order update [{'orderID': '4f364691-49a2-757f-babb-f068b2b25652', 'ordStatus': 'Filled', 'workingIndicator': False, 'leavesQty': 0, 'cumQty': 1, 'avgPx': 3779.5, 'clOrdID': '', 'account': 169818, 'symbol': 'XBTUSD', 'timestamp': '2019-01-04T16:29:44.807Z'}]
    position update [{'account': 169818, 'symbol': 'XBTUSD', 'currency': 'XBt', 'currentTimestamp': '2019-01-04T16:30:00.190Z', 'markPrice': 3755.65, 'timestamp': '2019-01-04T16:30:00.190Z', 'lastPrice': 3755.65, 'currentQty': -6, 'liquidationPrice': 1694915}]

    order insert [{'orderID': '358a6bdd-e6b7-4239-d581-f91812036e6e', 'clOrdID': '', 'clOrdLinkID': '', 'account': 169818, 'symbol': 'XBTUSD', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 7, 'price': 3779.5, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'USD', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': '', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'New', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 7, 'simpleCumQty': None, 'cumQty': 0, 'avgPx': None, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from testnet.bitmex.com', 'transactTime': '2019-01-04T16:32:49.468Z', 'timestamp': '2019-01-04T16:32:49.468Z'}]
    order update [{'orderID': '358a6bdd-e6b7-4239-d581-f91812036e6e', 'workingIndicator': True, 'clOrdID': '', 'account': 169818, 'symbol': 'XBTUSD', 'timestamp': '2019-01-04T16:32:49.468Z'}]
    position update [{'account': 169818, 'symbol': 'XBTUSD', 'currency': 'XBt', 'openOrderBuyQty': 7, 'openOrderBuyCost': -185213, 'grossOpenCost': 26459, 'riskValue': 186281, 'initMargin': 26519, 'timestamp': '2019-01-04T16:32:49.468Z', 'currentQty': -6, 'markPrice': 3754.12, 'liquidationPrice': 1694915}]
    order update [{'orderID': '358a6bdd-e6b7-4239-d581-f91812036e6e', 'ordStatus': 'Filled', 'workingIndicator': False, 'leavesQty': 0, 'cumQty': 7, 'avgPx': 3779.5, 'clOrdID': '', 'account': 169818, 'symbol': 'XBTUSD', 'timestamp': '2019-01-04T16:32:49.468Z'}]
    position update [{'account': 169818, 'symbol': 'XBTUSD', 'currency': 'XBt', 'openOrderBuyQty': 0, 'openOrderBuyCost': 0, 'execBuyQty': 8, 'execBuyCost': 211672, 'execQty': 8, 'execCost': -211672, 'execComm': 157, 'currentTimestamp': '2019-01-04T16:32:49.470Z', 'currentQty': 1, 'currentCost': -27243, 'currentComm': 564, 'realisedCost': -784, 'unrealisedCost': -26459, 'grossOpenCost': 0, 'grossExecCost': 26459, 'markValue': -26637, 'riskValue': 26637, 'homeNotional': 0.00026637, 'foreignNotional': -1, 'posCost': -26459, 'posCost2': -26459, 'posInit': 26459, 'posComm': 40, 'posLoss': 0, 'posMargin': 26499, 'posMaint': 173, 'initMargin': 0, 'maintMargin': 26321, 'realisedGrossPnl': 784, 'realisedPnl': 220, 'unrealisedGrossPnl': -178, 'unrealisedPnl': -178, 'unrealisedPnlPcnt': -0.0067, 'unrealisedRoePcnt': -0.0067, 'avgCostPrice': 3779.5, 'avgEntryPrice': 3779.5, 'breakEvenPrice': 3572.5, 'marginCallPrice': 1894.5, 'liquidationPrice': 1894.5, 'bankruptPrice': 1890, 'timestamp': '2019-01-04T16:32:49.470Z', 'lastValue': -26637, 'markPrice': 3754.12}]

    """
