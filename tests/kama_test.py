import pandas as pd



def vperiod(data, period):
    df = pd.DataFrame()
    data['abst'] = data['close'].diff(period).abs()
    data['volat'] = data.주가.diff().abs().rolling(period).sum()
    data['vperiod'] = (data['abst'] / data['volat'] * period).dropna().astype(int)
    df = pd.concat([df, data['vperiod']], axis=1)
    return df


def vmomentum(x):
    return a['close'].shift(x['vperiod'])[x.name]

a['vmomentum'] = a.apply(vmomentum, axis=1)

a['vperiod'] = vperiod(a, 12)
a.dropna(inplace=True)


a['profit'] = np.where(a.close.shift(1) > a.vmomentum.shift(1), a.close / a.close.shift(1), 1.03 ** (1 / 12)).cumprod()
a['현금혼합'] = np.where(a.close.shift(1) > a.vmomentum.shift(1), (a.close / a.close.shift(1) + 1.03 ** (1 / 12)) / 2, 1).cumprod()
