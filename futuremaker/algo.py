

class Algo(object):

    def update_candle(self, df, candle):
        """
        캔들이 업데이트되어 dict가 들어온다.
        :param df: pandas.DataFrame
        :param candle: dict
        :return:
        """
        pass

    def update_orderbook(self, orderbook):
        """
        orderbook이 업데이트되어 들어온다.
        {
            'symbol': 'XBTUSD',
            'timestamp': '2019-01-12T08: 07: 23.150Z',
            'bids': [
                [
                    3609.5,
                    1070
                ],
                ....
            ],
            'asks': [
                [
                    3610,
                    813
                ],
                ....
            ]
        }
        :return:
        """
        pass

    def update_order(self, order):
        """
        업데이트된 order 가 들어온다. nexus['order']['<orderID'] 로도 접근가능.
        :param order:
        :return:
        """
        pass

    def update_position(self, position):
        """
        업데이트된 position 이 들어온다. nexus['position'] 으로 접근한 객체와 동일하다.
        :param position:
        :return:
        """
        pass

    def send_telegram(self, text):
        pass