# data_analysis.py
import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib import rcParams

# ======================
# 中文字体设置
# ======================
rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 微软雅黑
rcParams['axes.unicode_minus'] = False            # 解决负号显示问题

# ======================
# 参数配置
# ======================
PRICE_DATA_PATH = "data/prices.csv"           # 股票价格数据
OUTPUT_DIR = "analysis_figures"               # 保存图表目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================
# 读取数据
# ======================
df_prices = pd.read_csv(PRICE_DATA_PATH, parse_dates=["date"])
stock_codes = df_prices['stock_code'].unique()
print(f"股票池数量: {len(stock_codes)}")

# ======================
# 股票价格统计分析
# ======================
stats = df_prices.groupby('stock_code')['close'].agg(['mean', 'std', 'min', 'max']).reset_index()
stats.to_csv(os.path.join(OUTPUT_DIR, "stock_price_stats.csv"), index=False)
print("每只股票价格统计已保存到 stock_price_stats.csv")

# 绘制价格均值直方图
plt.figure(figsize=(8,5))
plt.hist(stats['mean'], bins=20, color='#1f77b4', edgecolor='black')
plt.title("股票均价分布")
plt.xlabel("均价")
plt.ylabel("股票数量")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "price_mean_hist.png"), dpi=200)
plt.close()

# ======================
# 日收益率与波动性分析
# ======================
df_prices['daily_ret'] = df_prices.groupby('stock_code')['close'].pct_change()

vol_stats = df_prices.groupby('stock_code')['daily_ret'].agg(
    mean_ret='mean',
    std_ret='std',
    max_up='max',
    max_down='min'
).reset_index()
vol_stats.to_csv(os.path.join(OUTPUT_DIR, "stock_volatility_stats.csv"), index=False)
print("每只股票收益率波动性统计已保存到 stock_volatility_stats.csv")

# 波动率直方图
plt.figure(figsize=(8,5))
plt.hist(vol_stats['std_ret'].dropna(), bins=20, color='#1f77b4', edgecolor='black')
plt.title("股票日收益率标准差分布（波动率）")
plt.xlabel("日收益率标准差")
plt.ylabel("股票数量")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "volatility_hist.png"), dpi=200)
plt.close()

print(f"分析图表已保存到 {OUTPUT_DIR} 文件夹")
