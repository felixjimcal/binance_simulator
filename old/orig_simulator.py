#
# REQUIRES https://github.com/Binance-docs/binance-futures-connector-python
#

import pandas as pd
from binance.futures import Futures

client = Futures(key='<api_key>', secret='<api_secret>')

ohlc = client.klines("BTCUSDT", "1d", **{"limit": 3})
ohlc.pop()  # https://binance-docs.github.io/apidocs/futures/en/#kline-candlestick-data
df = pd.DataFrame(ohlc, columns=['OPEN', 'HIGH', 'LOW', 'CLOSE', '', '', '', '', '', '', '', ''])
print(ohlc)
