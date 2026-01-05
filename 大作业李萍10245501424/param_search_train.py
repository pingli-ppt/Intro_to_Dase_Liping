# param_search_train.py
import pandas as pd
import itertools
from backtest import run_backtest, performance_metrics

# 参数网格
PRICE_TRIGGERS = [0.03, 0.05, 0.07]
TRADE_RATIOS = [0.03, 0.05, 0.10]
MAX_POSITION_MULTS = [1.5, 2.0]

DATA_PATH = "data/prices.csv"
TRAIN_CSV = "train_param_results.csv"

def train_param_search():
    df_prices = pd.read_csv(DATA_PATH, parse_dates=['date'])
    results = []

    for pt, tr, mp in itertools.product(PRICE_TRIGGERS, TRADE_RATIOS, MAX_POSITION_MULTS):
        # 回测
        net_df = run_backtest(df_prices, price_trigger=pt, trade_ratio=tr, max_position_mult=mp)
        metrics = performance_metrics(net_df)

        results.append({
            'PRICE_TRIGGER': pt,
            'TRADE_RATIO': tr,
            'MAX_POSITION_MULT': mp,
            'Total Return': metrics['Total Return'],
            'Max Drawdown': metrics['Max Drawdown'],
            'Sharpe Ratio': metrics['Sharpe Ratio']
        })

    result_df = pd.DataFrame(results)
    result_df.to_csv(TRAIN_CSV, index=False)

    # 输出最优参数（按 Sharpe）
    best_row = result_df.sort_values('Sharpe Ratio', ascending=False).iloc[0]
    print("=== Best Parameters on Training Set ===")
    print(best_row)

    return result_df

if __name__ == "__main__":
    train_param_search()
