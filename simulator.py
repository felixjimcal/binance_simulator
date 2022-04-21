import datetime
import sys

import numpy as np
import pandas as pd
from binance.client import Client
from binance.enums import *

from utils import credentials

HIGH = 'high'
LOW = 'low'
TIMESTAMP = 'timestamp'
OPEN = 'open'
CLOSE = 'close'
VOLUME = 'volume'
CTM_STRING = 'ctm_string'

BUY = 'buy'
FIXED_RISK = 0.05
ATR = 'atr'
PLUS = 'plus'
MIN = 'minus'
LONG_LEGGED = 'll'
SUPPORTS = 'supports'
RESISTANCES = 'resistances'

MACD_1M = 'macd_1m'
MACD_SIGNAL_1M = 'macd_signal_1m'
MACD_HIST_1M = 'macd_hist_1m'

BALANCE = 300


def strategy_a(df_min, s):
    """

    :param df_min:
    :param s:
    :return:
    """
    try:
        last_buys = []
        my_balance = BALANCE
        wins = 0
        gains = 0
        losses = 0
        open_trades = 0
        closed_trades = 0
        min_amount = 0.001
        for i, row in df_min.iterrows():
            # Running out of money
            if my_balance <= 0:
                return "so", "RIP", round(my_balance, 2), row.ctmString

            if row['entry'] and isinstance(row.resistances, str):
                size_in_usdt = FIXED_RISK * my_balance * min_amount * row.close
                if 0 < size_in_usdt < my_balance and my_balance > (min_amount * row.close) and my_balance > (BALANCE * 0.20):
                    min_margin = round(0.004 * size_in_usdt, 2)
                    actual_margin = sum([li[6] for li in last_buys])
                    actual_profit = sum([round((row.close - li[0]) * li[3], 2) for li in last_buys])
                    free_margin = (my_balance - actual_margin) - actual_profit
                    if free_margin >= min_margin:
                        fees = round(((size_in_usdt * 0.04) / 100), 4)
                        buy_price = row.close + fees
                        sl = buy_price - (0.20 * buy_price)
                        res = list(map(float, row.resistances.replace('[', '').replace(']', '').split(",")))
                        tp = buy_price + 0.01 + size_in_usdt if not any(ele > buy_price for ele in res) else next(x[1] for x in enumerate(res) if x[1] > buy_price)
                        last_buys.append((buy_price, sl, tp, size_in_usdt, row.ctmString, row.timestamp, fees))
                        open_trades += 1
                        my_balance -= size_in_usdt

            for e, lb in enumerate(last_buys):
                last_buy = lb[0]
                stop_price = lb[1]
                tp = lb[2]
                size_in_usdt = lb[3]
                if row.low <= stop_price <= row.high:
                    result = (stop_price - last_buy) * (size_in_usdt / last_buy)
                    print(last_buys[e])
                    if result < 0:
                        losses += result
                    elif result > 0:
                        wins += result
                    my_balance += result
                    gains += result
                    del last_buys[e]
                    closed_trades += 1
                    continue
                if row.low <= tp <= row.high or row.high > tp:
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
                # if i + 1 < len(df_min) and datetime.datetime.utcfromtimestamp(row.timestamp / 1000).day != datetime.datetime.utcfromtimestamp(df_min.timestamp.iloc[i + 1] / 1000).day: # RISKY
                if datetime.datetime.utcfromtimestamp(lb[5] / 1000).day != datetime.datetime.utcfromtimestamp(row.timestamp / 1000).day:  # SAFE GAINS
                    result = (row.close - last_buy) * (size_in_usdt / last_buy)
                    if result <= 0:
                        continue
                    elif result > 0:
                        wins += result
                    my_balance += result
                    gains += result
                    del last_buys[e]
                    closed_trades += 1
                    continue
        trades = 'OT:', open_trades, 'CT', closed_trades
        margin_dates = df_min.ctmString[0], df_min.ctmString[len(df_min) - 1]
        return 'so', 'Real:', round(my_balance, 2), "Profit:", round(gains, 2), "Wins:", round(wins, 2), "Losses:", round(losses, 2), trades, margin_dates
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('Fail in so:', ex.args, 'line:', exc_tb.tb_lineno)


def apply_pivots(df_b, df_min):
    df_min['t'] = [datetime.datetime.utcfromtimestamp(x / 1000).day for x in df_min.timestamp]
    df_min[SUPPORTS] = np.nan
    df_min[RESISTANCES] = np.nan

    for _, day in df_b.iterrows():
        df_pivots_high = day.high
        df_pivots_low = day.low
        df_pivots_close = day.close
        decimals = 1
        pivot = round((df_pivots_high + df_pivots_low + df_pivots_close) / 3, decimals)
        resistance_1 = round(2 * pivot - df_pivots_low, decimals)
        resistance_2 = round(pivot + (df_pivots_high - df_pivots_low), decimals)
        resistance_3 = round(pivot + 2 * (df_pivots_high - df_pivots_low), decimals)
        resistances = sorted([pivot, resistance_1, resistance_2, resistance_3])
        support_1 = round(2 * pivot - df_pivots_high, decimals)
        support_2 = round(pivot - (df_pivots_high - df_pivots_low), decimals)
        support_3 = round(pivot - 2 * (df_pivots_high - df_pivots_low), decimals)
        supports = sorted([pivot, support_1, support_2, support_3], reverse=True)
        # week_day = datetime.datetime.fromtimestamp(day.ctm / 1000).weekday()

        # if day.ctm == df_b['close_time'].iloc[-1]:
        #     break

        # days = 1
        # if week_day == 4:
        #     days = 3
        # ctm_day = int((datetime.datetime.fromtimestamp(day.ctm / 1000) + datetime.timedelta(days=days)).strftime("%d"))

        minutes_index = df_min.index[df_min["t"] == (datetime.datetime.utcfromtimestamp(day.timestamp / 1000) + datetime.timedelta(days=1)).day].tolist()
        for i in minutes_index:
            df_min.at[i, SUPPORTS] = str(supports)
            df_min.at[i, RESISTANCES] = str(resistances)

    df_min = df_min.drop(['t'], axis=1)
    return df_min
    # ONLY FOR DEBUG
    # print(df_min[SUPPORTS].iloc[int(len(df_min)/2)], df_min[CTM_STRING].iloc[int(len(df_min)/2)])


def prepare_data(crypto_symbol):
    """

    :param crypto_symbol:
    :return:
    """
    try:
        end = datetime.datetime.today().now().strftime("%d/%m/%Y")
        start = (datetime.datetime.today() - datetime.timedelta(weeks=9)).strftime("%d/%m/%Y")
        candles_b = binance_client.futures_historical_klines(symbol=crypto_symbol, interval=KLINE_INTERVAL_1DAY, start_str=start, end_str=end)
        if not candles_b:
            return 'no data'
        df_day = pd.DataFrame(candles_b, columns=[TIMESTAMP, OPEN, HIGH, LOW, CLOSE, VOLUME, 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
        df_day = df_day.drop(['close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'], axis=1)
        df_day.insert(1, CTM_STRING, np.nan)
        df_day[CTM_STRING] = [str(datetime.datetime.utcfromtimestamp(x / 1000)) for x in df_day.timestamp]
        for col in df_day.columns[2:]:
            df_day[col] = pd.to_numeric(df_day[col])

        # candles_min = binance_client.futures_historical_klines(symbol=symbol, interval=KLINE_INTERVAL_15MINUTE, start_str=start, end_str=end)
        # if not candles_min:
        #     return 'no data'
        # df_min = pd.DataFrame(candles_min, columns=[TIMESTAMP, OPEN, HIGH, LOW, CLOSE, VOLUME, 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
        # df_min = df_min.drop(['close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'], axis=1)
        # df_min.insert(1, CTM_STRING, np.nan)
        # df_min[CTM_STRING] = [str(datetime.datetime.utcfromtimestamp(x / 1000)) for x in df_min.timestamp]
        # for col in df_min.columns[2:]:
        #     df_min[col] = pd.to_numeric(df_min[col])

        # candles_hour = binance_client.futures_historical_klines(symbol=symbol, interval=KLINE_INTERVAL_1HOUR, start_str=start, end_str=end)
        # if not candles_hour:
        #     return 'no data'
        # df_hour = pd.DataFrame(candles_hour, columns=[TIMESTAMP, OPEN, HIGH, LOW, CLOSE, VOLUME, 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
        # df_hour = df_hour.drop(['close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'], axis=1)
        # df_hour.insert(1, CTM_STRING, np.nan)
        # df_hour[CTM_STRING] = [str(datetime.datetime.utcfromtimestamp(x / 1000)) for x in df_hour.timestamp]
        # for col in df_hour.columns[2:]:
        #     df_hour[col] = pd.to_numeric(df_hour[col])

        # Pivots
        # df_min = apply_pivots(df_day, df_min)

        print(crypto_symbol, strategy_a(df_day, crypto_symbol))
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('Fail in prepare_data:', ex.args, 'line:', exc_tb.tb_lineno, crypto_symbol)


if __name__ == "__main__":
    binance_client = Client(credentials.BINANCE_API_FUTURES, credentials.BINANCE_API_FUTURES_SECRET, testnet=False)

    # all_symbols = binance_client.get_products()['data']
    # symbols = []
    # for t in all_symbols:
    #     if "USDT" in t['s']:
    #         symbols.append(t['s'])

    # https://cryptowat.ch/es-es/correlations
    symbols = ['DOGEUSDT', 'LUNAUSDT', 'SOLUSDT', 'XMRUSDT', 'ZECUSDT']
    for symbol in symbols:
        prepare_data(symbol)
