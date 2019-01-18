# Futuremaker

Algorithm Trading Bot Library

## Supported Exchanges

* BitMex

Belows are comming soon..
* Binance
* Bithumb
* Upbit

## Futuremaker is Fun

```python
# algo.py
from futuremaker.bitmex.algo import Algo

class AlertGo(Algo):

    def __init__(self):
        super(AlertGo, self).__init__(symbol='XBTUSD')

    def update_candle(self, df, candle):
        print(candle)

bot = AlertGo()
bot.run()
```

## Easy to Setup

```bash
$ pip install futuremaker
$ python algo.py
```
## Resources

* Algorithm tutorial (#TBD)
* Documentation (#TBD)
* Pypi - https://pypi.org/project/futuremaker/

## Contribute
If you've found a bug, let me know. If you would like to participate in the development together, please email hello@systom.io at any time.

