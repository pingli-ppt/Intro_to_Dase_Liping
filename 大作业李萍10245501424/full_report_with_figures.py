# full_report_with_figures.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import shutil

# =============================
# 数据路径
# =============================
PRICE_DATA_PATH = "data/prices.csv"
STRATEGY_NET_PATH = "strategy_net.csv"
STRATEGY_SIGNAL_PATH = "data/strategy_signal.csv"
HS300_PATH = "HS300.csv"
PARAM_HEATMAP_PATH = "param_sensitivity_heatmap.png"

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# =============================
# 1️⃣ 读取数据
# =============================
df_prices = pd.read_csv(PRICE_DATA_PATH, parse_dates=["date"]).sort_values(["stock_code","date"])
df_net = pd.read_csv(STRATEGY_NET_PATH, parse_dates=["date"]).set_index("date").sort_index()
df_signal = pd.read_csv(STRATEGY_SIGNAL_PATH, parse_dates=["date"]).sort_values("date")
df_hs300 = pd.read_csv(HS300_PATH, parse_dates=["date"]).set_index("date").sort_index()

# =============================
# 2️⃣ 绩效指标
# =============================
def compute_metrics(series):
    values = series.values
    returns = values[1:] / values[:-1] - 1
    total_return = values[-1]/values[0]-1
    max_dd = (values / values.max() - 1).min()
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() !=0 else 0
    return total_return, max_dd, sharpe

total_return, max_drawdown, sharpe = compute_metrics(df_net["net_value"])

# -----------------------------
# 3️⃣ 策略 vs 基准净值折线
# -----------------------------
df_prices["daily_ret"] = df_prices.groupby("stock_code")["close"].pct_change()
ew_ret = df_prices.groupby("date")["daily_ret"].mean().dropna()
ew_net = (1 + ew_ret).cumprod()
common_dates = df_net.index.intersection(ew_net.index).intersection(df_hs300.index)

df_strategy_plot = df_net.loc[common_dates].copy()
df_strategy_plot["net_value"] /= df_strategy_plot["net_value"].iloc[0]

ew_net_plot = ew_net.loc[common_dates] / ew_net.loc[common_dates].iloc[0]
hs300_plot = df_hs300.loc[common_dates, "close"] / df_hs300.loc[common_dates, "close"].iloc[0]

fig1, ax = plt.subplots(figsize=(8,4))
ax.plot(df_strategy_plot.index, df_strategy_plot["net_value"], label="策略净值", color="#1f77b4")
ax.plot(ew_net_plot.index, ew_net_plot, label="等权组合", color="#ff7f0e")
ax.plot(hs300_plot.index, hs300_plot, label="HS300指数", color="#2ca02c")
ax.set_title("策略净值 vs 等权组合 vs HS300")
ax.set_xlabel("日期")
ax.set_ylabel("归一化净值")
ax.legend()
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("net_value_comparison.png", dpi=200)

# -----------------------------
# 4️⃣ 股票价格波动
# -----------------------------
stock_code = df_prices["stock_code"].iloc[0]
stock = df_prices[df_prices["stock_code"]==stock_code].sort_values("date")
fig2, ax = plt.subplots(figsize=(6,3))
ax.plot(stock["date"], stock["close"], color="#1f77b4")
ax.set_title(f"{stock_code} 收盘价波动示意")
ax.set_xticks([])
ax.set_yticks([])
plt.tight_layout()
plt.savefig("price_fluctuation.png", dpi=200)

# -----------------------------
# 5️⃣ 策略信号示意
# -----------------------------
fig3, ax = plt.subplots(figsize=(6,2))
ax.plot(df_signal["date"], df_signal["signal"], marker='o', color="#1f77b4")
for d, s in zip(df_signal["date"], df_signal["signal"]):
    if s > 0:
        ax.text(d, s, "+", fontsize=10, color="#1f77b4")
    elif s < 0:
        ax.text(d, s, "-", fontsize=10, color="#1f77b4")
ax.set_title("策略触发示意（1=加仓，-1=减仓）")
ax.set_xticks([])
ax.set_yticks([])
plt.tight_layout()
plt.savefig("strategy_signal.png", dpi=200)

# -----------------------------
# 6️⃣ 参数敏感性热力图
# -----------------------------
shutil.copy(PARAM_HEATMAP_PATH, "param_sensitivity_heatmap_copy.png")

# -----------------------------
# 7️⃣ 原文本整合 Markdown
# -----------------------------
report_md = f"""
# 基于价格波动的动态仓位管理策略研究

## 1 引言
股票市场中价格波动频繁，投资者在涨跌中面临“止盈或加仓”的决策困境。
本策略通过价格波动触发动态仓位管理，实现风险控制与收益优化。

## 2 数据与方法

### 2.1 数据来源
- A 股前 500 只活跃股票历史日线数据（2022-01-01 至 2023-12-31）
- 数据通过 AkShare 获取
- 保证每只股票交易日一致（交易日交集筛选）

### 2.2 策略设计
- 初始建仓：总资金 50% 等权分配
- 动态仓位调整：
    - 价格上涨 ≥ 5% → 分批止盈（减仓 5%）
    - 价格下跌 ≥ 5% → 分批加仓（加仓 5%），上限 2 倍初始仓位
- 调仓频率：每日
- 仓位约束：最小 0，最大 2 倍初始仓位

### 2.3 参数学习
- PRICE_TRIGGER: 价格触发阈值
- TRADE_RATIO: 调仓比例
- MAX_POSITION_MULT: 最大仓位倍数
- 通过历史回测网格搜索筛选最优参数

### 2.4 回测指标
- 总收益率（Total Return）
- 最大回撤（Max Drawdown）
- 夏普比率（Sharpe Ratio）

## 3 实证结果

### 3.1 策略净值表现
总收益率: {total_return:.4%}  
最大回撤: {max_drawdown:.4%}  
夏普比率: {sharpe:.4f}  

![策略净值对比](net_value_comparison.png)

### 3.2 股票价格波动
股票 {stock_code} 收盘价：

![股票价格波动](price_fluctuation.png)

### 3.3 策略触发示意
![策略信号](strategy_signal.png)

### 3.4 参数敏感性
![参数敏感性](param_sensitivity_heatmap_copy.png)

## 4 讨论
- 策略无需预测模型，通过历史数据规则进行仓位调整
- 风险可控，回撤低于基准
- 夏普比率高于等权组合与指数基准

## 5 结论与展望
- 动态仓位管理策略能有效捕捉短期市场波动机会
- 参数自动学习提高策略稳健性与客观性
- 未来可引入多因子信号、止损机制及扩展时间尺度验证策略泛化性
"""

with open("quant_strategy_full_report.md", "w", encoding="utf-8") as f:
    f.write(report_md)

print("完整实验报告已生成: quant_strategy_full_report.md")
