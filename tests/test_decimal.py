from decimal import Decimal, ROUND_DOWN


def test_float():
    position_quantity = 0
    quantity = 2.281
    togo = quantity
    buy_unit = 0.01
    while togo > 0:
        tobuy = min(buy_unit, togo)
        print(f'sell order {tobuy}')
        togo -= tobuy
        position_quantity -= tobuy
        message = f'SELL > {position_quantity}/{quantity}'
        print(message)


def test_decimal():
    position_quantity = Decimal(1.0)
    quantity = Decimal(str(2.289))
    togo = Decimal(quantity)
    buy_unit = 0.01
    while togo > 0:
        tobuy = Decimal(min(buy_unit, togo))
        tobuy = tobuy.quantize(Decimal(str(1/10**3)), rounding=ROUND_DOWN)
        print(f'sell order {tobuy}')
        togo -= tobuy
        position_quantity -= tobuy
        message = f'SELL > {togo}/{position_quantity}/{quantity}'
        print(message)
    print(float(position_quantity) * 1.0)

test_decimal()