# Futuremaker

Futuremaker는 파이썬 pandas 로 쉽게 만들수 있는 암호화폐 트레이딩 봇입니다.
 
Futuremaker is a progressive cryptocurrency algorithm trading library based on Python.

라이선스 : [MIT licensed](https://opensource.org/licenses/MIT).

pypi: [latest version](https://pypi.org/project/futuremaker/) at pypi. 

## How to install

```
$ git clone https://github.com/songaal/futuremaker
```

또는 

```
$ pip install futuremaker
```

## Supported Exchanges

마진위주 (Margins) 

* [Binance](https://www.binance.com/)
* [Bybit](https://www.bybit.com/)
* [BitMex](https://www.bitmex.com/)

## Futuremaker is Fun

```python
# algo.py
from futuremaker.algo import Algo

class AlertGo(Algo):

    def __init__(self):
        super(AlertGo, self).__init__(symbol='BTCUSDT')

    def update_candle(self, df, candle):
        print(candle)

bot = AlertGo()
bot.run()
```

## Contribute

함께 개발하고 싶은 분은 songaal@gmail.com 으로 연락주세요.

If you've found a bug, let me know. If you would like to participate in the development together, please email songaal@gmail.com at any time.

