import pandas as pd

# -------------------------------
# 参数设置
# -------------------------------
PRICE_DATA_PATH = "data/prices.csv"          # 股票价格 CSV
STRATEGY_SIGNAL_PATH = "data/strategy_signal.csv"  # 输出信号 CSV
THRESHOLD_UP = 0.03   # 价格上涨5%触发加仓
THRESHOLD_DOWN = -0.03 # 价格下跌5%触发减仓

# -------------------------------
# 1️⃣ 读取价格数据
# -------------------------------
df = pd.read_csv(PRICE_DATA_PATH, parse_dates=["date"])
stock_code = df["stock_code"].iloc[0]   # 取第一只股票示例
stock = df[df["stock_code"]==stock_code].sort_values("date").copy()

# -------------------------------
# 2️⃣ 计算每日涨跌幅
# -------------------------------
stock["daily_return"] = stock["close"].pct_change()

# -------------------------------
# 3️⃣ 根据阈值生成信号
# -------------------------------
def generate_signal(ret):
    if ret > THRESHOLD_UP:
        return 1    # 加仓
    elif ret < THRESHOLD_DOWN:
        return -1   # 减仓
    else:
        return 0    # 不操作

stock["signal"] = stock["daily_return"].apply(generate_signal)

# -------------------------------
# 4️⃣ 保存为 CSV
# -------------------------------
df_signal = stock[["date", "stock_code", "signal"]]
df_signal.to_csv(STRATEGY_SIGNAL_PATH, index=False)
print(f"策略信号已生成: {STRATEGY_SIGNAL_PATH}")
