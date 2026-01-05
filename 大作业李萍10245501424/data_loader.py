# data_loader.py加载本地 CSV 数据，并划分训练集和测试集。
import pandas as pd

def load_price_data(path):
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values(["stock_code", "date"])
    
    # 保证每只股票长度一致
    counts = df.groupby("stock_code")["date"].count()
    valid_codes = counts[counts == counts.max()].index
    df = df[df["stock_code"].isin(valid_codes)]
    
    return df

def split_train_test(df, split_date):
    train_df = df[df["date"] <= split_date].copy()
    test_df = df[df["date"] > split_date].copy()
    return train_df, test_df
