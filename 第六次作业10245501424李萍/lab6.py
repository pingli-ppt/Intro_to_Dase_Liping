import pandas as pd
import numpy as np
import pymysql
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error
import joblib
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from scikeras.wrappers import KerasRegressor
from tensorflow.keras.callbacks import EarlyStopping

plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams['axes.unicode_minus'] = False

# 读取数据函数保持不变
def get_full_rank_data():
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="liping1231",
        database="academic_rankings"
    )
    
    sql = """
    SELECT 
        ip.research_field,
        ip.web_of_science_documents AS docs,
        ip.cites,
        ip.cites_per_paper,
        ip.top_papers,
        i.country_region,
        ip.global_rank
    FROM institution_performance ip
    JOIN institutions i ON ip.institution_id = i.id
    WHERE ip.global_rank IS NOT NULL
    """
    full_data = pd.read_sql(sql, conn)
    conn.close()
    
    full_data = full_data[
        (full_data["docs"] > 0) & 
        (full_data["cites_per_paper"] >= 0)
    ]
    return full_data

full_data = get_full_rank_data()
print(f"全量学科数据规模：{full_data.shape[0]}条样本，{full_data.shape[1]}个特征")

# 数据划分保持不变
X = full_data[["research_field", "docs", "cites", "cites_per_paper", "top_papers", "country_region"]]
y = full_data["global_rank"]

X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.4, random_state=42
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=42
)

print(f"\n数据集划分：")
print(f"训练集：{X_train.shape[0]}条（60%）")
print(f"验证集：{X_val.shape[0]}条（20%）")
print(f"测试集：{X_test.shape[0]}条（20%）")

# 特征预处理保持不变
numeric_features = ["docs", "cites", "cites_per_paper", "top_papers"]
categorical_features = ["research_field", "country_region"]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
    ])

# 预处理数据（为深度学习模型准备）
X_train_processed = preprocessor.fit_transform(X_train)
X_val_processed = preprocessor.transform(X_val)
X_test_processed = preprocessor.transform(X_test)

# 获取输入特征数量
input_dim = X_train_processed.shape[1]
print(f"\n预处理后特征维度：{input_dim}")

# 定义深度学习模型
def build_deep_learning_model():
    model = Sequential([
        Dense(128, activation='relu', input_dim=input_dim),
        BatchNormalization(),
        Dropout(0.3),
        
        Dense(64, activation='relu'),
        BatchNormalization(),
        Dropout(0.2),
        
        Dense(32, activation='relu'),
        Dropout(0.1),
        
        Dense(1)  # 输出层，预测排名
    ])
    
    # 编译模型
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='mean_squared_error',
        metrics=['mean_absolute_error', 'mean_absolute_percentage_error']
    )
    
    return model

# 创建Keras回归器（适配scikit-learn接口）
dl_model = KerasRegressor(
    build_fn=build_deep_learning_model,
    epochs=100,
    batch_size=32,
    verbose=1
)

# 定义早停策略防止过拟合
early_stopping = EarlyStopping(
    monitor='val_loss',
    patience=10,
    restore_best_weights=True
)

# 训练深度学习模型
print("\n=== 训练深度学习模型 ===")
dl_model.fit(
    X_train_processed, y_train,
    validation_data=(X_val_processed, y_val),
    callbacks=[early_stopping],
    epochs=100,
    batch_size=32
)

# 绘制训练过程中的损失曲线
plt.figure(figsize=(12, 5))

# 绘制MSE损失
plt.subplot(1, 2, 1)
plt.plot(dl_model.history_['loss'], label='训练损失')  # 改为 history_
plt.plot(dl_model.history_['val_loss'], label='验证损失')
plt.title('模型损失曲线')
plt.xlabel('Epoch')
plt.ylabel('MSE')
plt.legend()

# 绘制MAE
plt.subplot(1, 2, 2)
plt.plot(dl_model.history_['mean_absolute_error'], label='训练MAE')  # 改为 history_
plt.plot(dl_model.history_['val_mean_absolute_error'], label='验证MAE')
plt.title('模型MAE曲线')
plt.xlabel('Epoch')
plt.ylabel('MAE')
plt.legend()

plt.tight_layout()
plt.savefig("dl_training_curves.png")
plt.close()

# 原有模型训练（线性回归和随机森林）
lr_pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("regressor", LinearRegression())
])

rf_pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("regressor", RandomForestRegressor(n_estimators=100, random_state=42))
])

print("\n=== 训练传统模型 ===")
lr_pipeline.fit(X_train, y_train)
rf_pipeline.fit(X_train, y_train)

# 模型评估函数（增加MAPE指标）
def evaluate_model(model, X, y, model_name, is_dl=False):
    if is_dl:
        y_pred = model.predict(X).flatten()
    else:
        y_pred = model.predict(X)
    
    mse = mean_squared_error(y, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y, y_pred)
    mape = mean_absolute_percentage_error(y, y_pred) * 100  # 转换为百分比
    r2 = r2_score(y, y_pred)
    
    print(f"\n{model_name}测试集评估：")
    print(f"均方误差（MSE）：{mse:.2f}")
    print(f"均方根误差（RMSE）：{rmse:.2f}")
    print(f"平均绝对误差（MAE）：{mae:.2f}")
    print(f"平均绝对百分比误差（MAPE）：{mape:.2f}%")
    print(f"决定系数（R²）：{r2:.4f}")
    
    return {"mse": mse, "rmse": rmse, "mae": mae, "mape": mape, "r2": r2, "y_pred": y_pred}

# 评估所有模型
dl_results = evaluate_model(dl_model, X_test_processed, y_test, "深度学习模型", is_dl=True)
lr_results = evaluate_model(lr_pipeline, X_test, y_test, "线性回归")
rf_results = evaluate_model(rf_pipeline, X_test, y_test, "随机森林")

# 比较模型性能
models = ["线性回归", "随机森林", "深度学习"]
metrics = ["mse", "rmse", "mae", "mape"]
metric_names = ["MSE", "RMSE", "MAE", "MAPE(%)"]

plt.figure(figsize=(16, 10))
for i, metric in enumerate(metrics):
    values = [lr_results[metric], rf_results[metric], dl_results[metric]]
    plt.subplot(2, 2, i+1)
    plt.bar(models, values, color=['blue', 'green', 'orange'])
    plt.title(f'不同模型的{metric_names[i]}比较')
    plt.ylabel(metric_names[i])
    for j, v in enumerate(values):
        plt.text(j, v + 0.05, f'{v:.2f}', ha='center')

plt.tight_layout()
plt.savefig("model_comparison.png")
plt.close()

# 可视化最佳模型预测结果
best_model_name = min(
    [("线性回归", lr_results["mse"]), 
     ("随机森林", rf_results["mse"]), 
     ("深度学习", dl_results["mse"])],
    key=lambda x: x[1]
)[0]

if best_model_name == "深度学习":
    y_pred = dl_results["y_pred"]
elif best_model_name == "随机森林":
    y_pred = rf_results["y_pred"]
else:
    y_pred = lr_results["y_pred"]

plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.5, label="预测值vs真实值")
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--", label="理想预测线")
plt.xlabel("真实全球排名")
plt.ylabel("预测全球排名")
plt.title(f"{best_model_name}模型预测结果")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("best_model_prediction.png")
print("\n最佳模型预测结果可视化图已保存为：best_model_prediction.png")

# 保存模型
joblib.dump(lr_pipeline, "lr_subject_rank_model.joblib")
joblib.dump(rf_pipeline, "rf_subject_rank_model.joblib")
# 保存Keras模型
dl_model.model_.save("dl_subject_rank_model.h5")  
print("\n所有模型已保存")

# 深度学习模型预测函数
def predict_with_dl(subject, docs, cites, cites_per_paper, top_papers, country_region):
    new_data = pd.DataFrame({
        "research_field": [subject],
        "docs": [docs],
        "cites": [cites],
        "cites_per_paper": [cites_per_paper],
        "top_papers": [top_papers],
        "country_region": [country_region]
    })
    
    # 预处理新数据
    new_data_processed = preprocessor.transform(new_data)
    # 预测排名
    predicted_rank = dl_model.predict(new_data_processed)[0][0]
    return round(predicted_rank)

# 示例预测
pred_rank_dl = predict_with_dl(
    subject="Education",
    docs=1200,
    cites=15000,
    cites_per_paper=12.5,
    top_papers=35,
    country_region="China"
)
print(f"\n深度学习模型示例预测：中国某高校教育学学科预测排名为：第{pred_rank_dl}名")
