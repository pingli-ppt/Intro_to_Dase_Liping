# metrics.py
import numpy as np
import pandas as pd

def performance_metrics(net_value: pd.Series):
    """
    计算组合净值序列的绩效指标
    net_value: pd.Series，组合净值
    """
    daily_ret = net_value.pct_change().dropna()
    total_return = net_value.iloc[-1] - 1
    cum_max = net_value.cummax()
    drawdown = net_value / cum_max - 1
    max_drawdown = drawdown.min()
    sharpe = (daily_ret.mean() / daily_ret.std() * np.sqrt(252)
              if daily_ret.std() != 0 else 0)
    return {
        "Total Return": total_return,
        "Max Drawdown": max_drawdown,
        "Sharpe Ratio": sharpe
    }
