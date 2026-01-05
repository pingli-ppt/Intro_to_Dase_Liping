# benchmark_analysis.py基准对比
import pandas as pd
import numpy as np
import akshare as ak
import matplotlib.pyplot as plt
import os

# ======================
# 参数
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRICE_PATH = os.path.join(BASE_DIR, "data", "prices.csv")

START_DATE = pd.to_datetime("2022-01-01")
END_DATE = pd.to_datetime("2023-12-31")

RISK_FREE_RATE = 0.02  # 年化无风险利率


# ======================
# 工具函数
# ======================
def performance_metrics(net_value: pd.Series):
    daily_ret = net_value.pct_change().dropna()

    total_return = net_value.iloc[-1] - 1

    cum_max = net_value.cummax()
    drawdown = net_value / cum_max - 1
    max_drawdown = drawdown.min()

    sharpe = (
        (daily_ret.mean() * 252 - RISK_FREE_RATE) /
        (daily_ret.std() * np.sqrt(252))
        if daily_ret.std() != 0 else 0
    )

    return {
        "Total Return": float(total_return),
        "Max Drawdown": float(max_drawdown),
        "Sharpe Ratio": float(sharpe)
    }


# ======================
# 等权组合基准
# ======================
def equal_weight_benchmark():
    df = pd.read_csv(PRICE_PATH)
    df["date"] = pd.to_datetime(df["date"])

    df = df.sort_values(["stock_code", "date"])
    df["daily_ret"] = df.groupby("stock_code")["close"].pct_change()

    ew_ret = (
        df.groupby("date")["daily_ret"]
        .mean()
        .dropna()
    )

    net_value = (1 + ew_ret).cumprod()
    net_value.name = "EqualWeight"
    return net_value


# ======================
# 沪深300指数
# ======================
def hs300_benchmark():
    df = ak.stock_zh_index_daily(symbol="sh000300")

    # === 明确处理日期 ===
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]

    # === 用 close 直接算净值（避免少一天）===
    net_value = df.set_index("date")["close"]
    net_value = net_value / net_value.iloc[0]
    net_value.name = "HS300"

    return net_value


# ======================
# 策略净值
# ======================
def load_strategy_net():
    df = pd.read_csv("strategy_net.csv")
    df["date"] = pd.to_datetime(df["date"])

    net = df.set_index("date")["net_value"]
    net.name = "Strategy"
    return net


# ======================
# 主流程
# ======================
def main():
    # === 1. 加载净值 ===
    strategy_net = load_strategy_net()
    equal_weight_net = equal_weight_benchmark()
    hs300_net = hs300_benchmark()

    # === 2. 调试信息 ===
    print("Strategy rows:", len(strategy_net))
    print("EqualWeight rows:", len(equal_weight_net))
    print("HS300 rows:", len(hs300_net))

    print("Strategy date range:", strategy_net.index.min(), strategy_net.index.max())
    print("EqualWeight date range:", equal_weight_net.index.min(), equal_weight_net.index.max())
    print("HS300 date range:", hs300_net.index.min(), hs300_net.index.max())

    # === 3. 对齐日期 ===
    compare = pd.concat(
        [strategy_net, equal_weight_net, hs300_net],
        axis=1,
        join="inner"
    )

    if compare.empty:
        raise ValueError("❌ 三条净值曲线没有重合日期")

    # === 4. 统一起点 ===
    compare = compare / compare.iloc[0]

    # === 5. 输出指标 ===
    print("\n=== Performance Comparison ===\n")
    for col in compare.columns:
        print(col, performance_metrics(compare[col]))

    # === 6. 画图 ===
    compare.plot(figsize=(10, 6), title="Strategy vs Benchmarks")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()

