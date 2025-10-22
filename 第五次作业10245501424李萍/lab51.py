# 1. 导入库（文档Sklearn库模块，含模型、预处理、评估）
import pandas as pd
import numpy as np
import pymysql
from sklearn.model_selection import train_test_split, cross_val_score  # 文档留出法、交叉验证
from sklearn.preprocessing import StandardScaler, OneHotEncoder  # 文档预处理
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline  # 流程化建模（适配PPT展示）
from sklearn.linear_model import LinearRegression  # 文档线性回归
from sklearn.ensemble import RandomForestRegressor  # 文档决策树扩展（集成模型）
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score  # 文档回归评估指标
import joblib  # 文档模型保存方法
import matplotlib.pyplot as plt  # 可视化（适配PPT）
import matplotlib.pyplot as plt


plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示异常
# 2. 从本地数据库读取全量学科排名数据
def get_full_rank_data():
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="liping1231",
        database="academic_rankings"
    )
    # 数据库配置（请替换为实际参数）

    sql = """
    SELECT 
        ip.research_field,
        ip.web_of_science_documents AS docs,
        ip.cites,
        ip.cites_per_paper,
        ip.top_papers,
        i.country_region,
        ip.global_rank  # 目标变量（排名，越小越好）
    FROM institution_performance ip
    JOIN institutions i ON ip.institution_id = i.id
    WHERE ip.global_rank IS NOT NULL  # 过滤无排名数据
    """
    full_data = pd.read_sql(sql, conn)
    conn.close()
    # 数据清洗（文档数据预处理第一步：处理异常值）
    full_data = full_data[
        (full_data["docs"] > 0) &  # 发文量>0
        (full_data["cites_per_paper"] >= 0)  # 篇均被引非负
    ]
    return full_data

full_data = get_full_rank_data()
print(f"全量学科数据规模：{full_data.shape[0]}条样本，{full_data.shape[1]}个特征")

# 3. 数据划分（文档要求：训练集60%、测试集20%、随机划分）
# 特征（X）与目标变量（y）定义
X = full_data[["research_field", "docs", "cites", "cites_per_paper", "top_papers", "country_region"]]
y = full_data["global_rank"]  # 目标：预测全球排名

# 随机划分（文档留出法，random_state保证可复现）
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.4, random_state=42  # 先分60%训练集，剩余40%分测试集和验证集
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=42  # 剩余40%分为20%验证集、20%测试集
)

print(f"\n数据集划分：")
print(f"训练集：{X_train.shape[0]}条（60%）")
print(f"验证集：{X_val.shape[0]}条（20%）")
print(f"测试集：{X_test.shape[0]}条（20%）")

# 4. 特征预处理（文档预处理逻辑：数值特征标准化、分类特征编码）
# 定义特征类型
numeric_features = ["docs", "cites", "cites_per_paper", "top_papers"]  # 数值特征
categorical_features = ["research_field", "country_region"]  # 分类特征

# 预处理流水线（文档Sklearn Pipeline应用，简化流程）
preprocessor = ColumnTransformer(
    transformers=[
        # 数值特征：标准化
        ("num", StandardScaler(), numeric_features),
        # 分类特征：独热编码（忽略未知类别，避免过拟合）
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
    ])

# 5. 模型构建与训练（文档推荐算法：线性回归、随机森林）
# （1）线性回归模型（文档基础回归算法）
lr_pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("regressor", LinearRegression())
])

# （2）随机森林回归模型（文档决策树扩展，处理非线性关系）
rf_pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("regressor", RandomForestRegressor(n_estimators=100, random_state=42))  # 100棵树
])

# 6. 模型训练与交叉验证（文档交叉验证法，评估泛化能力）
print("\n=== 模型训练与评估 ===")

# 训练线性回归
lr_pipeline.fit(X_train, y_train)
# 5折交叉验证（文档交叉验证法，cv=5）
lr_cv_scores = cross_val_score(lr_pipeline, X_val, y_val, cv=5, scoring="neg_mean_squared_error")
lr_cv_rmse = np.sqrt(-lr_cv_scores.mean())  # 交叉验证RMSE

# 训练随机森林
rf_pipeline.fit(X_train, y_train)
rf_cv_scores = cross_val_score(rf_pipeline, X_val, y_val, cv=5, scoring="neg_mean_squared_error")
rf_cv_rmse = np.sqrt(-rf_cv_scores.mean())

print(f"线性回归交叉验证RMSE：{lr_cv_rmse:.2f}")
print(f"随机森林交叉验证RMSE：{rf_cv_rmse:.2f}")
# 选择最优模型（RMSE越小越好）
best_model = rf_pipeline if rf_cv_rmse < lr_cv_rmse else lr_pipeline
print(f"选择最优模型：{'随机森林回归' if rf_cv_rmse < lr_cv_rmse else '线性回归'}")

# 7. 模型测试与评估（文档测试集评估逻辑）
y_pred = best_model.predict(X_test)
# 计算评估指标（文档回归指标：MSE、RMSE、MAE、R²）
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\n最优模型测试集评估：")
print(f"均方误差（MSE）：{mse:.2f}")
print(f"均方根误差（RMSE）：{rmse:.2f}（平均预测偏差）")
print(f"平均绝对误差（MAE）：{mae:.2f}")
print(f"决定系数（R²）：{r2:.4f}（越接近1越好）")

# 8. 可视化预测结果（适配PPT展示，文档未直接提及但为常规分析步骤）
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.5, label="预测值vs真实值")
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--", label="理想预测线")
plt.xlabel("真实全球排名")
plt.ylabel("预测全球排名")
plt.title(f"{('随机森林' if rf_cv_rmse < lr_cv_rmse else '线性回归')}模型预测结果")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("rank_prediction_result.png")  # 保存图片，用于PPT
print("\n预测结果可视化图已保存为：rank_prediction_result.png")

# 9. 模型保存（文档Joblib方法，适合大型模型）
joblib.dump(best_model, "subject_rank_prediction_model.joblib")
print("\n排名预测模型已保存为：subject_rank_prediction_model.joblib")

# 10. 模型应用示例（预测新学科排名）
def predict_new_subject(subject, docs, cites, cites_per_paper, top_papers, country_region):
    # 构建新样本
    new_data = pd.DataFrame({
        "research_field": [subject],
        "docs": [docs],
        "cites": [cites],
        "cites_per_paper": [cites_per_paper],
        "top_papers": [top_papers],
        "country_region": [country_region]
    })
    # 预测排名
    predicted_rank = best_model.predict(new_data)[0]
    return round(predicted_rank)

# 示例：预测某高校“教育学”学科排名（假设参数）
pred_rank = predict_new_subject(
    subject="Education",
    docs=1200,
    cites=15000,
    cites_per_paper=12.5,
    top_papers=35,
    country_region="China"
)
print(f"\n示例预测：中国某高校教育学学科预测排名为：第{pred_rank}名")