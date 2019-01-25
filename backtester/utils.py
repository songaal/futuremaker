import ccxt
import ccxt.async_support as ccxt_async

def ccxt_exchange(exchange_id, apiKey=None, secret=None, async=True):

    opt = {}

    if apiKey is not None and secret is not None:
        opt.update({
            'apiKey': apiKey,
            'secret': secret,
        })
    if async:
        exchange = getattr(ccxt_async, exchange_id)(opt)
    else:
        exchange = getattr(ccxt, exchange_id)(opt)
    exchange.substituteCommonCurrencyCodes = False

    return exchange
