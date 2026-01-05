# param_sensitivity_heatmap.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

TRAIN_CSV = "train_param_results.csv"
df = pd.read_csv(TRAIN_CSV)

# 只看 MAX_POSITION_MULT = 2.0 的平面
df_plot = df[df['MAX_POSITION_MULT'] == 2.0]

pivot = df_plot.pivot(index='PRICE_TRIGGER',
                      columns='TRADE_RATIO',
                      values='Sharpe Ratio')

plt.figure(figsize=(6, 4))
sns.heatmap(pivot, annot=True, fmt=".3f", cmap="YlGnBu", cbar_kws={'label': 'Sharpe Ratio'})
plt.title("Parameter Sensitivity Heatmap (Sharpe)")
plt.xlabel("TRADE_RATIO")
plt.ylabel("PRICE_TRIGGER")
plt.tight_layout()
plt.savefig("param_sensitivity_heatmap.png", dpi=300)
plt.show()
