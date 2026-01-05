# fetch_prices.py从 AkShare 获取 A 股前 N 只股票的历史日线数据，
# 并做初步清洗，保证每只股票交易日一致。
import os
import time
import akshare as ak
import pandas as pd


# ========================
# 参数配置
# ========================
START_DATE = "20220101"
END_DATE = "20231231"
N_STOCKS = 500
OUTPUT_PATH = "data/prices.csv"


def main():
    print("Step 1: 获取股票列表...")
    stock_list = ak.stock_zh_a_spot_em()
    codes = stock_list["代码"].tolist()[:N_STOCKS]
    print(f"股票数量: {len(codes)}")

    all_data = []

    print("Step 2: 拉取历史行情数据...")
    for i, code in enumerate(codes, 1):
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=START_DATE,
                end_date=END_DATE,
                adjust="qfq"
            )
            df = df[["日期", "收盘"]]
            df.columns = ["date", "close"]
            df["stock_code"] = code
            all_data.append(df)

            if i % 20 == 0:
                print(f"已完成 {i}/{len(codes)}")

            time.sleep(0.2)  # 防止请求过快

        except Exception as e:
            print(f"{code} 获取失败")

    print("Step 3: 合并数据...")
    price_df = pd.concat(all_data, ignore_index=True)
    price_df["date"] = pd.to_datetime(price_df["date"])

    print("Step 4: 交易日一致性筛选...")
    counts = price_df.groupby("stock_code")["date"].count()
    max_len = counts.max()
    valid_codes = counts[counts == max_len].index
    price_df = price_df[price_df["stock_code"].isin(valid_codes)]

    price_df = price_df.sort_values(["date", "stock_code"])

    print("Step 5: 保存数据...")
    os.makedirs("data", exist_ok=True)
    price_df.to_csv(OUTPUT_PATH, index=False)

    print("完成 ✅")
    print(f"最终股票数: {price_df['stock_code'].nunique()}")
    print(f"数据保存路径: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
