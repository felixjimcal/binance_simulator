def apply_so(df, df_2=None):
    """

    """
    try:
        df_2['ma_50'] = talib.MA(df_2.close, timeperiod=50).dropna()
        df_2['ma_200'] = talib.MA(df_2.close, timeperiod=200).dropna()
        df_2['over_ma'] = np.where(df_2['ma_50'] > df_2['ma_200'], True, False)
        df_2 = df_2.drop(['ma_50', 'ma_200'], axis=1)

        slow_k, slow_d = talib.STOCH(df.high, df.low, df.close, fastk_period=50, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
        df['t'] = [str(datetime.datetime.utcfromtimestamp(x / 1000).day) + '_' + str(datetime.datetime.utcfromtimestamp(x / 1000).hour) + '_' + str(datetime.datetime.utcfromtimestamp(x / 1000).minute) for x in df.timestamp]
        df['slow_k'] = round(slow_k, 2)
        df['slow_d'] = round(slow_d, 2)
        df['lower_20'] = np.where((df['slow_k'] < 20) & (df['slow_d'] < 20) & (abs(df['slow_k'] - df['slow_d']) < 2), True, False)

        if df_2 is not None:
            slow_k_3, slow_d_3 = talib.STOCH(df_2.high, df_2.low, df_2.close, fastk_period=50, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
            df_2['t'] = [str(datetime.datetime.utcfromtimestamp(x / 1000).day) + '_' + str(datetime.datetime.utcfromtimestamp(x / 1000).hour) + '_' + str(datetime.datetime.utcfromtimestamp(x / 1000).minute) for x in df_2.timestamp]
            df_2['slow_k_3'] = round(slow_k_3, 2)
            df_2['slow_d_3'] = round(slow_d_3, 2)
            df_2['lower_80'] = np.where((df_2['slow_k_3'] < 20) & (df_2['slow_d_3'] < 20), True, False)

            df['entry'] = False
            for i, d_h in df_2.iterrows():
                hours_index = df.index[(df["t"] == d_h['t']) & (df['lower_20']) & (d_h['lower_80']) & (d_h['over_ma'])].tolist()
                for j in hours_index:
                    df.at[j, 'entry'] = True
        df = df.drop(['t', 'lower_20'], axis=1)
        return df
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('Fail in so:', ex.args, 'line:', exc_tb.tb_lineno)
