#
# REQUIRES https://github.com/Binance-docs/binance-futures-connector-python
#
import datetime
import sys

import numpy as np
import pandas as pd
from binance.futures import Futures

HIGH = 'high'
LOW = 'low'
TIMESTAMP = 'timestamp'
OPEN = 'open'
CLOSE = 'close'
VOLUME = 'volume'
CTM_STRING = 'ctm_string'

BUY = 'buy'
FIXED_RISK = 0.05

BALANCE = 300


def strategy_tendencies(data_frm, symbl):
    """
    https://www.sersansistemas.com/sistemas-de-trading/familias-sistemas/sistemas-nemesis/

    Operar cuando:
    Roturas por volatilidad, cierra con STOPLOSS o cierre porgramado o cambio tendencia
    """
    try:
        last_buys = []
        my_balance = BALANCE
        wins = 0
        gains = 0
        losses = 0
        open_trades = 0
        closed_trades = 0
        for i, row in data_frm.iterrows():
            # Running out of money
            if my_balance <= 0:
                return "so", "RIP", round(my_balance, 2), row.ctmString

        print('nope')
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('Fail in so:', ex.args, 'line:', exc_tb.tb_lineno)


def prepare_data(crypto_symbol):
    """

    """
    ohlc = client.klines(crypto_symbol, "1d", **{"limit": 15})  # **{"limit": 1500})
    ohlc.pop()  # https://binance-docs.github.io/apidocs/futures/en/#kline-candlestick-data
    df_day = pd.DataFrame(ohlc, columns=[TIMESTAMP, OPEN, HIGH, LOW, CLOSE, VOLUME, 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
    df_day = df_day.drop(['close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'], axis=1)
    df_day.insert(1, CTM_STRING, np.nan)
    df_day[CTM_STRING] = [str(datetime.datetime.utcfromtimestamp(x / 1000)) for x in df_day.timestamp]

    print(crypto_symbol, strategy_tendencies(df_day, crypto_symbol))
    # print(crypto_symbol, strategy_(df_day, crypto_symbol))
    # print(crypto_symbol, strategy_a(df_day, crypto_symbol))


if __name__ == "__main__":
    client = Futures(key='<api_key>', secret='<api_secret>')

    symbols = ['DOGEUSDT', 'LUNAUSDT', 'SOLUSDT', 'XMRUSDT', 'ZECUSDT']
    for symbol in symbols:
        prepare_data(symbol)
