# Futuremaker

Futuremaker is a progressive cryptocurrency algorithm trading library based on Python. It's [MIT licensed](https://opensource.org/licenses/MIT).

Check [latest version](https://pypi.org/project/futuremaker/) at pypi. 

## How to install

```
$ pip install futuremaker
```

## Supported Exchanges

* [BitMex](https://www.bitmex.com/)

Belows are comming soon..
* [Binance](https://www.binance.com/)
* [Bithumb](https://www.bithumb.com/)
* [Upbit](https://upbit.com/)

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

## Contribute
If you've found a bug, let me know. If you would like to participate in the development together, please email hello@systom.io at any time.

