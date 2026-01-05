# test_evaluation.py — 测试集评估（Out-of-Sample Performance）
import pandas as pd
import config

from data_loader import load_price_data, split_train_test
from backtest import run_backtest
from metrics import performance_metrics  # 注意这里导入函数名与 metrics.py 一致

DATA_PATH = "data/prices.csv"
SPLIT_DATE = "2023-06-30"


def test_with_best_params():
    # 读取训练集最优参数
    best_param = pd.read_csv("train_param_results.csv").iloc[0]

    price_trigger = best_param["PRICE_TRIGGER"]
    trade_ratio = best_param["TRADE_RATIO"]
    max_position_mult = best_param["MAX_POSITION_MULT"]

    # 读取数据并划分训练/测试集
    df = load_price_data(DATA_PATH)
    _, test_df = split_train_test(df, SPLIT_DATE)

    # 运行回测（传入最优参数）
    net_df = run_backtest(
        test_df,
        price_trigger=price_trigger,
        trade_ratio=trade_ratio,
        max_position_mult=max_position_mult
    )

    # 计算绩效指标
    metrics = performance_metrics(net_df["net_value"])

    # 打印结果
    print("\n=== Test Set Performance (Out-of-Sample) ===")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}")

    # 保存测试集净值
    net_df.to_csv("test_net_value.csv", index=False)


if __name__ == "__main__":
    test_with_best_params()
