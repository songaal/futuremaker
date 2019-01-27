import pandas as pd


def zigzag(df, deviation=0.70):
    upper_target = 1 + deviation / 100
    down_target = 1 - deviation / 100

    index_data = df.index[0]
    price_data = df.Close[index_data]
    trend = None

    zz_index, zz_price = [index_data], [price_data]

    for idx, high, low in zip(df.index, df.High, df.Low):
        # 처음시작.
        if trend is None:
            if high / price_data > upper_target:
                trend = 1
            elif low / price_data < down_target:
                trend = -1
        # 오름추세
        elif trend == 1:
            # 신규 고점발견
            if high > price_data:
                index_data, price_data = idx, high
            # 변곡점
            elif low / price_data < down_target:
                zz_index.append(index_data)
                zz_price.append(price_data)

                trend, index_data, price_data = -1, idx, low
        # Trend is down
        else:
            # New L
            if low < price_data:
                index_data, price_data = idx, low
            # Reversal
            elif high / price_data > upper_target:
                zz_index.append(index_data)
                zz_price.append(price_data)

                trend, index_data, price_data = 1, idx, high

    # Extrapolate the current trend
    if zz_index[-1] != df.index[-1]:
        zz_index.append(df.index[-1])

        if trend is None:
            zz_price.append(df.Close[zz_index[-1]])
        elif trend == 1:
            zz_price.append(df.High[zz_index[-1]])
        else:
            zz_price.append(df.Low[zz_index[-1]])

    return pd.Series(zz_price, index=zz_index)


def zigzag2(df, deviation=0.05, spread=1):
    upper_target = 1 + deviation / 100
    down_target = 1 - deviation / 100

    index_data = df.index[0]
    price_data = df.Close[index_data]
    trend = None

    zz_high_index, zz_high = [index_data], [price_data]
    zz_low_index, zz_low = [index_data], [price_data]

    for idx, close in zip(df.index, df.Close):
        # 처음시작.
        if trend is None:
            if close / price_data > upper_target or close - price_data >= spread:
                trend = 1
            elif close / price_data < down_target or price_data - close >= spread:
                trend = -1
        # 오름추세
        elif trend == 1:
            # 신규 고점발견
            if close > price_data:
                index_data, price_data = idx, close
            # 변곡점
            # 변곡점은 조금만 내려와도 기록한다.
            elif close / price_data < down_target or price_data - close >= spread: # spread달러이상
                zz_high_index.append(index_data)
                zz_high.append(price_data)

                trend, index_data, price_data = -1, idx, close
        # 하락추세.
        else:
            # 새로운 저점.
            if close < price_data:
                index_data, price_data = idx, close
            # 변곡점
            elif close / price_data > upper_target or close - price_data >= spread:
                zz_low_index.append(index_data)
                zz_low.append(price_data)

                trend, index_data, price_data = 1, idx, close

    # 현재추세를 추정.
    # 마지막 인덱스가 zz 인덱스와 동일하지 않다면 넣어준다.
    idx = df.index[-1]
    if zz_high_index[-1] != idx:
        zz_high_index.append(idx)
        zz_high.append(df.Close[idx])

    if zz_low_index[-1] != idx:
        zz_low_index.append(idx)
        zz_low.append(df.Close[idx])

    return pd.Series(data=zz_high, index=zz_high_index), pd.Series(data=zz_low, index=zz_low_index)