# strategy.py定义交易信号和执行逻辑
from config import PRICE_TRIGGER, TRADE_RATIO, MAX_POSITION_MULT

def trade_signal(position, price):
    last_price = position.last_trade_price
    if last_price is None:
        return None

    price_change = (price - last_price) / last_price

    if price_change >= PRICE_TRIGGER:
        return "sell"
    elif price_change <= -PRICE_TRIGGER:
        return "buy"
    return None


def execute_trade(signal, position, price, init_value):
    if signal == "sell" and position.shares > 0:
        sell_shares = int(position.shares * TRADE_RATIO)
        position.shares -= sell_shares
        position.cash += sell_shares * price
        position.last_trade_price = price

    elif signal == "buy":
        max_value = init_value * MAX_POSITION_MULT
        current_value = position.market_value(price)
        if current_value < max_value:
            buy_value = init_value * TRADE_RATIO
            buy_shares = int(buy_value // price)
            cost = buy_shares * price
            if position.cash >= cost:
                position.cash -= cost
                position.shares += buy_shares
                position.avg_price = price
                position.last_trade_price = price

