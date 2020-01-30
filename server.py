import asyncio

from sanic import Sanic
from sanic.response import json

app = Sanic(name='bot')


@app.route("/")
async def test(request):
    return json({"hello": "world"})


@app.route("/backtest")
async def run_bot(request):
    from futuremaker.bot import Bot
    from bots.sample import AlertGo
    from bots.sample import Yoil
    from bots.sample import ExchangeAPI
    api = ExchangeAPI()
    year = 2019
    bot = Bot(api, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
              candle_period='1h',
              backtest=True, test_start=f'{year}-01-01', test_end=f'{year}-12-31',
              test_data='candle_data/BINANCE_BTCUSDT, 60.csv'
              # test_data='../candle_data/BITFINEX_BTCUSD, 120.csv'
              # test_data='../candle_data/BINANCE_ETCUSDT, 60.csv'static=StaticHandler(paths=['/your_static_dir', '/second_static_dir'])
              # test_data='../candle_data/BITFINEX_ETHUSD, 60.csv'
              )

    algo = AlertGo(week_start=Yoil.MON, hour_start=0, long_rate=0.4, short_rate=0.4)
    asyncio.get_event_loop().create_task(bot.run(algo))
    return json({"bot": "sample"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
