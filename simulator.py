#
# REQUIRES https://github.com/Binance-docs/binance-futures-connector-python
#
import datetime
import sys

import numpy as np
import pandas as pd
import talib
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
BALANCE_PILLOW = 0.20


def strategy_tendencies(df, symbl):
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
        min_amount = 1
        for i, row in df.iterrows():
            # Running out of money
            if my_balance <= 0:
                return "strategy_tendencies", "RIP", round(my_balance, 2), row.ctm_string

            if row['entry']:
                size_in_usdt = 1  # FIXED_RISK * my_balance * min_amount * row.close
                if 0 < size_in_usdt < my_balance and my_balance > (min_amount * row.close) and my_balance > (BALANCE * BALANCE_PILLOW):
                    min_margin = round(0.004 * size_in_usdt, 2)
                    actual_margin = sum([li[6] for li in last_buys])
                    actual_profit = sum([round((row.close - li[0]) * li[3], 2) for li in last_buys])
                    free_margin = (my_balance - actual_margin) - actual_profit
                    if free_margin >= min_margin:
                        fees = round(((size_in_usdt * 0.04) / 100), 4)
                        buy_price = row.close + fees
                        sl = buy_price - (0.20 * buy_price)
                        res = 0  # list(map(float, row.resistances.replace('[', '').replace(']', '').split(",")))
                        tp = 0  # buy_price + (0.5 * buy_price)  # buy_price + 0.01 + size_in_usdt if not any(ele > buy_price for ele in res) else next(x[1] for x in enumerate(res) if x[1] > buy_price)
                        last_buys.append((buy_price, sl, tp, size_in_usdt, row.ctm_string, row.timestamp, fees))
                        open_trades += 1
                        my_balance -= size_in_usdt

            for e, lb in enumerate(last_buys):
                last_buy = lb[0]
                stop_price = lb[1]
                tp = lb[2]
                size_in_usdt = lb[3]
                if row.low <= stop_price <= row.high:
                    result = (stop_price - last_buy) * (size_in_usdt / last_buy)
                    # print(last_buys[e])
                    if result < 0:
                        losses += result
                    elif result > 0:
                        wins += result
                    my_balance += result
                    gains += result
                    del last_buys[e]
                    closed_trades += 1
                    continue
                # if row.low <= tp <= row.high or row.high > tp:
                if row['RSI_OVER_70']:
                    result = (row.close - last_buy) * (size_in_usdt / last_buy)
                    if result < 0:
                        continue
                    elif result > 0:
                        wins += result
                    my_balance += result
                    gains += result
                    del last_buys[e]
                    closed_trades += 1
                    continue
        trades = 'OT:', open_trades, 'CT', closed_trades
        margin_dates = df.ctm_string[0], df.ctm_string[len(df) - 1]
        return 'so', 'Real:', round(my_balance, 2), "Profit:", round(gains, 2), "Wins:", round(wins, 2), "Losses:", round(losses, 2), trades, margin_dates

    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('Fail in so:', ex.args, 'line:', exc_tb.tb_lineno)


def prepare_data(crypto_symbol):
    """

    """
    ohlc = client.klines(crypto_symbol, "1d", **{"limit": 1500})  # limit 1500
    ohlc.pop()  # https://binance-docs.github.io/apidocs/futures/en/#kline-candlestick-data
    df_day = pd.DataFrame(ohlc, columns=[TIMESTAMP, OPEN, HIGH, LOW, CLOSE, VOLUME, 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
    df_day = df_day.drop(['close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'], axis=1)
    df_day.insert(1, CTM_STRING, np.nan)
    df_day[CTM_STRING] = [str(datetime.datetime.utcfromtimestamp(x / 1000)) for x in df_day.timestamp]
    for col in df_day.columns[2:]:
        df_day[col] = pd.to_numeric(df_day[col])

    df_day['EMA_S'] = round(talib.EMA(df_day.close, 20), 4)
    df_day['EMA_M'] = round(talib.EMA(df_day.close, 70), 4)
    df_day['EMA_L'] = round(talib.EMA(df_day.close, 100), 4)

    # Es interesante plantear un código para detectar picos y divergencias en el RSI
    # el RSI baja y el precio sube en un plazo de tiempo más grande, divergencia
    df_day['RSI'] = round(talib.RSI(df_day.close, 14), 4)
    df_day['RSI_UNDER_30'] = np.where(df_day.RSI < 30, True, False)
    df_day['RSI_OVER_70'] = np.where(df_day.RSI > 90, True, False)

    # https://www.youtube.com/watch?v=IeasOiEua-4&t=0s&ab_channel=An%C3%A1lisisT%C3%A9cnicoSt.
    # upper, middle, lower = talib.BBANDS(df_day.close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    # df_day['BB_U'] = round(upper, 4)
    # df_day['BB_M'] = round(middle, 4)
    # df_day['BB_L'] = round(lower, 4)
    # df_day['L_BB_L'] = np.where(df_day.low <= df_day.BB_L, True, False)

    # 7, 10, 6, 6
    # sto_k, sto_d = talib.STOCHRSI(df_day.close, timeperiod=10, fastk_period=7, fastd_period=6, fastd_matype=6)
    # df_day['sto_k'] = round(sto_k, 4)
    # df_day['sto_d'] = round(sto_d, 4)

    # df_day['entry'] = np.where(, True, False)
    print(crypto_symbol, strategy_tendencies(df_day, crypto_symbol))
    # print(crypto_symbol, strategy_(df_day, crypto_symbol))
    # print(crypto_symbol, strategy_a(df_day, crypto_symbol))


if __name__ == "__main__":
    client = Futures(key='<api_key>', secret='<api_secret>')

    symbols = ['DOGEUSDT' , 'LUNAUSDT', 'SOLUSDT', 'XMRUSDT', 'ZECUSDT']
    for symbol in symbols:
        prepare_data(symbol)
