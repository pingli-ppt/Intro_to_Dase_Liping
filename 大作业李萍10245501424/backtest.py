# backtest.py
import pandas as pd
import numpy as np
from config import TOTAL_CAPITAL, INIT_RATIO, RISK_FREE_RATE

def run_backtest(price_df: pd.DataFrame,
                 price_trigger: float,
                 trade_ratio: float,
                 max_position_mult: float) -> pd.DataFrame:
    """
    回测逻辑：
    price_df: ['date', 'stock_code', 'close']
    返回 net_df: ['net_value']，日期索引
    """
    price_df = price_df.sort_values(['date','stock_code']).copy()
    stocks = price_df['stock_code'].unique()
    dates = sorted(price_df['date'].unique())

    cash = TOTAL_CAPITAL * (1 - INIT_RATIO)
    base_position_value = TOTAL_CAPITAL * INIT_RATIO / len(stocks)
    positions = {s: base_position_value for s in stocks}
    last_price = {}
    net_values = []

    for date in dates:
        daily = price_df[price_df['date'] == date]
        total_value = cash

        for _, row in daily.iterrows():
            code = row['stock_code']
            price = row['close']

            # 初次记录价格
            if code not in last_price:
                last_price[code] = price
                total_value += positions[code]
                continue

            prev_price = last_price[code]
            ret = (price - prev_price) / prev_price
            pos_value = positions[code]

            # 卖出逻辑
            if ret >= price_trigger:
                target = max(pos_value * (1 - trade_ratio*2), 0)
                cash += pos_value - target
                positions[code] = target
            # 买入逻辑
            elif ret <= -price_trigger:
                target = min(pos_value * (1 + trade_ratio*2), max_position_mult * base_position_value)
                cost = target - pos_value
                if cash >= cost:
                    cash -= cost
                    positions[code] = target
            else:
                # 微调仓位 ±5% 基仓位
                change = np.random.uniform(-0.05, 0.05) * base_position_value
                target = min(max(pos_value + change, 0), max_position_mult * base_position_value)
                delta = target - positions[code]
                if delta > 0 and cash >= delta:
                    cash -= delta
                    positions[code] = target
                elif delta < 0:
                    cash -= delta
                    positions[code] = target

            last_price[code] = price
            total_value += positions[code]

        net_values.append({'date': date, 'net_value': total_value / TOTAL_CAPITAL})

    net_df = pd.DataFrame(net_values).set_index('date')
    return net_df

def performance_metrics(net_df: pd.DataFrame) -> dict:
    daily_ret = net_df['net_value'].pct_change().dropna()
    total_return = net_df['net_value'].iloc[-1] - 1
    cum_max = net_df['net_value'].cummax()
    drawdown = net_df['net_value'] / cum_max - 1
    max_drawdown = drawdown.min()
    sharpe = ((daily_ret.mean() - RISK_FREE_RATE / 252) / daily_ret.std() * np.sqrt(252)
              if daily_ret.std() != 0 else 0)
    metrics = {
        'Total Return': total_return,
        'Max Drawdown': max_drawdown,
        'Sharpe Ratio': sharpe
    }
    return metrics

# 调试用
if __name__ == "__main__":
    df = pd.read_csv("data/prices.csv", parse_dates=['date'])
    net_df = run_backtest(df, price_trigger=0.05, trade_ratio=0.05, max_position_mult=2.0)
    metrics = performance_metrics(net_df)
    print(metrics)
    net_df.to_csv("strategy_net.csv")
