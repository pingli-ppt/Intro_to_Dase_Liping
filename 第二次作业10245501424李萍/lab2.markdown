## 项目概述
这是一个完整的房价数据分析项目，包含数据加载、缺失值处理、相关性分析、异常值检测与处理、数据标准化和离散化等步骤。

## 代码原理和效果分析

### 1. 数据加载和初步探索

```python
# 加载数据
df = pd.read_csv('train.csv')
print("数据集形状（行数, 列数）：", df.shape)
```

**原理**：使用pandas加载CSV格式的房价数据，查看数据规模。

**效果**：输出数据集的基本信息，为后续分析奠定基础。

![缺失值统计](缺失值统计.png)

### 2. 缺失值处理策略

#### 分类属性处理：
```python
# 删除高缺失比例属性（>50%）
high_missing_cat_cols = ['PoolQC', 'MiscFeature', 'Alley', 'Fence', 'FireplaceQu']
df = df.drop(columns=high_missing_cat_cols)
# 剩余分类属性用"Unknown"填充
cat_cols = df.select_dtypes(include=['object']).columns
```

**原理**：
- 对于缺失率超过50%的分类属性直接删除，因为这些属性信息量太少
- 剩余分类属性用"Unknown"填充，保留数据完整性

#### 数值属性处理（KNN填充）：
```python
knn_imputer = KNNImputer(n_neighbors=5)
num_data_imputed = knn_imputer.fit_transform(num_data)
```

**原理**：KNN算法基于相似样本的值来填充缺失值。对于每个缺失值，找到k个最相似的样本，用它们的平均值填充。

**效果**：既考虑了数据的分布特征，又保持了数据间的相关性。

![缺失值处理效果](缺失值处理效果.png)

### 3. 相关性分析

```python
corr_matrix = num_df.corr()
sale_price_corr = corr_matrix['SalePrice'].sort_values(ascending=False)
```

**原理**：计算皮尔逊相关系数，衡量数值变量间的线性相关程度。

**输出结果示例**：
```
与房价（SalePrice）相关性前20的特征：
SalePrice       1.000000
OverallQual     0.790982
GrLivArea       0.708624
GarageCars      0.680625
GarageArea      0.623431
...（其他特征）
```

**多重共线性检测**：发现如'GarageCars'与'GarageArea'等高相关特征对，这些在建模时需要注意避免多重共线性问题。

![特征间的相关性分析](特征间的相关性分析.png)

![特征相关性热力图](特征相关性热力图.png)

### 4. 异常值检测与处理

#### Z-score检测：
```python
def detect_outliers_zscore(data, col, threshold=3):
    mean = data[col].mean()
    std = data[col].std()
    z_scores = (data[col] - mean) / std
    outliers = data[abs(z_scores) > threshold]
```

**原理**：Z-score衡量数据点距离均值的标准差倍数。Z-score绝对值大于3被视为异常值。

#### 缩尾处理（Winsorization）：
```python
def handle_outliers_zscore(data, col, threshold=3):
    upper_bound = mean + threshold * std
    lower_bound = mean - threshold * std
    data[col] = np.where(data[col] > upper_bound, upper_bound, data[col])
```

**原理**：将超出3倍标准差的极端值替换为边界值，既减少了异常值影响，又保留了数据分布形态。

![异常值箱线图](异常值箱线图.png)

![异常值处理后箱线图](异常值处理后箱线图.png)

### 5. 数据标准化

```python
scaler = StandardScaler()
sale_price_scaled = scaler.fit_transform(sale_price)
```

**原理**：Z-score标准化，将数据转换为均值为0、标准差为1的分布。
- 公式：$z = \frac{x - \mu}{\sigma}$

**效果**：消除量纲影响，使不同尺度的数据可以进行比较。

![房价标准化前后分布](房价标准化前后分布.png)

### 6. 数据离散化

```python
discretizer = KBinsDiscretizer(n_bins=5, encode='ordinal', strategy='quantile')
```

**原理**：等频离散化，将连续变量分成5个区间，每个区间包含大致相同数量的样本。

**输出结果示例**：
```
房价离散化区间（美元）：
类别0：[34900, 129975]，样本数：292
类别1：[129975, 163000]，样本数：292
类别2：[163000, 214000]，样本数：292
类别3：[214000, 266925]，样本数：292
类别4：[266925, 755000]，样本数：292
```

![房价离散化类别分布](房价离散化类别分布.png)

### 7. 与房价最相关的三个特征：

1. **OverallQual（整体质量）** - 相关性0.79
   - **业务意义**：房屋质量是购房决策的核心因素
   - **可视化效果**：箱线图清晰显示质量等级与房价的正相关关系

2. **GrLivArea（地上居住面积）** - 相关性0.71  
   - **业务意义**：面积是房价的基础决定因素
   - **可视化效果**：散点图展示明显的正相关趋势

3. **GarageCars（车库容量）** - 相关性0.68
   - **业务意义**：反映房屋配套设施水平
   - **可视化效果**：箱线图显示车库容量越大，房价越高

![房价Top3相关特征关系图](房价Top3相关特征关系图.png)
## 项目价值

## 数据内部更深入的关系思考

```python
# 思考：特征不是孤立的，而是存在层级结构
"""
房价影响因素的层级关系：
第一层（直接因素）：OverallQual, GrLivArea, GarageCars
    ↓
第二层（间接因素）：GarageArea, TotalBsmtSF, 1stFlrSF
    ↓
第三层（基础因素）：YearBuilt, LotArea, Neighborhood
"""
```

###  建立了完整的数据分析思维框架**

**收获**：理解了数据分析的标准流程：
```
数据加载 → 探索性分析 → 数据清洗 → 特征工程 → 洞察发现
```

### 🔑 **技术层面**
- 掌握了pandas、sklearn等核心库的实际应用
- 学会了数据可视化的最佳实践
- 理解了机器学习预处理的关键步骤
