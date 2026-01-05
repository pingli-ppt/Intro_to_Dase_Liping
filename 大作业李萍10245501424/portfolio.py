# portfolio.py管理组合持仓、现金和市值。

class Position:
    def __init__(self, init_cash):
        self.cash = init_cash
        self.shares = 0
        self.avg_price = 0
        self.last_trade_price = None

    def market_value(self, price):
        return self.shares * price


class Portfolio:
    def __init__(self, total_capital, n_stocks):
        self.cash = total_capital
        self.positions = {}
        self.n_stocks = n_stocks

    def init_position(self, stock, price, init_cash):
        shares = init_cash // price
        pos = Position(init_cash - shares * price)
        pos.shares = shares
        pos.avg_price = price
        pos.last_trade_price = price
        self.positions[stock] = pos
        self.cash -= shares * price

