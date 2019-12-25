# from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.KlineApi()
symbol = 'symbol_example' # str | Contract type.
interval = 'interval_example' # str | Kline interval.
_from = 8.14 # float | from timestamp.
limit = 'limit_example' # str | Contract type. (optional)

try:
    # Query historical kline.
    api_response = api_instance.kline_get(symbol, interval, _from, limit=limit)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling KlineApi->kline_get: %s\n" % e)