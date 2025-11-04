import os
import glob
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, mean_absolute_error
import matplotlib.pyplot as plt


# 1. 数据预处理工具（支持多学科特征）
class TabularPreprocessor:
    def __init__(self, numerical_cols, categorical_cols):
        self.numerical_cols = numerical_cols
        self.categorical_cols = categorical_cols
        self.num_scaler = StandardScaler()
        self.cat_encoders = {col: LabelEncoder() for col in categorical_cols}
        self.cat_dims = {}  # 类别特征基数（含学科）
    
    def fit(self, df):
        self.num_scaler.fit(df[self.numerical_cols])
        for col in self.categorical_cols:
            df[col] = df[col].fillna('Unknown')
            self.cat_encoders[col].fit(df[col])
            self.cat_dims[col] = len(self.cat_encoders[col].classes_) + 1  # +1 留作未知类别
        return self
    
    def transform(self, df):
        num_features = self.num_scaler.transform(df[self.numerical_cols])
        cat_features = []
        for col in self.categorical_cols:
            df_col = df[col].fillna('Unknown')
            mask = ~df_col.isin(self.cat_encoders[col].classes_)
            df_col[mask] = 'Unknown'
            encoded = self.cat_encoders[col].transform(df_col)
            cat_features.append(encoded)
        return num_features, cat_features


# 2. 数据集类（不变，支持多特征）
class TabularDataset(Dataset):
    def __init__(self, num_features, cat_features, targets):
        self.num_features = torch.tensor(num_features, dtype=torch.float32)
        self.cat_features = [torch.tensor(cat, dtype=torch.long) for cat in cat_features]
        self.targets = torch.tensor(targets, dtype=torch.float32)  # 排名为连续值
    
    def __len__(self):
        return len(self.num_features)
    
    def __getitem__(self, idx):
        return (self.num_features[idx], [cat[idx] for cat in self.cat_features], self.targets[idx])


# 3. TabNet核心模块（不变，支持多类别特征）
class FeatureTransformer(nn.Module):
    def __init__(self, input_dim, output_dim, n_d=8, n_a=8, dropout=0.1):
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(input_dim, 2 * (n_d + n_a)),
            nn.BatchNorm1d(2 * (n_d + n_a)),
            nn.GLU(dim=1)
        )
        self.dropout = nn.Dropout(dropout)
        self.residual = nn.Linear(input_dim, n_d + n_a) if input_dim != n_d + n_a else nn.Identity()
    
    def forward(self, x):
        residual = self.residual(x)
        x = self.block(x)
        x = self.dropout(x)
        return x + residual


class AttentiveTransformer(nn.Module):
    def __init__(self, input_dim, n_features, relaxation_factor=1.3):
        super().__init__()
        self.relaxation_factor = relaxation_factor
        self.layer = nn.Sequential(
            nn.Linear(input_dim, n_features),
            nn.BatchNorm1d(n_features)
        )
    
    def forward(self, x, prior=None):
        x = self.layer(x)
        if prior is not None:
            x = x - self.relaxation_factor * prior
        mask = torch.softmax(x, dim=1)
        return mask


# 4. TabNet完整模型（不变，适配多特征）
class TabNet(nn.Module):
    def __init__(self, 
                 num_numerical, 
                 cat_dims, 
                 embed_dim=8, 
                 n_d=8, n_a=8, 
                 n_steps=3, 
                 gamma=1.3, 
                 output_dim=1, 
                 task='regression'):
        super().__init__()
        self.num_numerical = num_numerical
        self.cat_dims = cat_dims
        self.embed_dim = embed_dim
        self.n_d = n_d
        self.n_a = n_a
        self.n_steps = n_steps
        self.task = task
        self.output_dim = output_dim
        
        self.cat_embeddings = nn.ModuleDict()
        for col, dim in cat_dims.items():
            self.cat_embeddings[col] = nn.Embedding(dim, embed_dim, padding_idx=dim-1)
        
        input_dim = num_numerical + len(cat_dims) * embed_dim
        self.initial_transformer = FeatureTransformer(input_dim, n_d + n_a, n_d, n_a)
        self.step_transformers = nn.ModuleList([
            FeatureTransformer(n_d, n_d + n_a, n_d, n_a) for _ in range(n_steps)
        ])
        self.attentive_transformers = nn.ModuleList([
            AttentiveTransformer(n_a, input_dim, relaxation_factor=gamma) for _ in range(n_steps)
        ])
        self.output_layer = nn.Linear(n_d, output_dim)
        self.feature_importances = None
    
    def forward(self, x_num, x_cat):
        cat_embeds = []
        for i, (col, embed) in enumerate(self.cat_embeddings.items()):
            cat_embeds.append(embed(x_cat[i]))
        cat_embeds = torch.cat(cat_embeds, dim=1)
        x = torch.cat([x_num, cat_embeds], dim=1)
        batch_size, input_dim = x.shape
        
        x_transformed = self.initial_transformer(x)
        d = x_transformed[:, :self.n_d]
        a = x_transformed[:, self.n_d:]
        
        output = torch.zeros(batch_size, self.n_d, device=x.device)
        prior = torch.zeros(batch_size, input_dim, device=x.device)
        self.feature_importances = torch.zeros(batch_size, input_dim, device=x.device)
        
        for step in range(self.n_steps):
            mask = self.attentive_transformers[step](a, prior)
            self.feature_importances += mask
            x_selected = x * mask
            prior = mask
            x_transformed = self.step_transformers[step](d)
            d = x_transformed[:, :self.n_d]
            a = x_transformed[:, self.n_d:]
            output += d * (1.0 / self.n_steps)
        
        logits = self.output_layer(output)
        return logits, self.feature_importances


# 5. 训练与评估工具（支持按学科评估）
class TabNetTrainer:
    def __init__(self, model, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.model = model.to(device)
        self.device = device
        self.optimizer = optim.Adam(model.parameters(), lr=0.0001)  # 同时减小学习率至0.0005（核心修改4）
    
    def train_epoch(self, dataloader):
        self.model.train()
        total_loss = 0.0
        for batch in dataloader:
            x_num, x_cat, y = batch
            x_num = x_num.to(self.device)
            x_cat = [cat.to(self.device) for cat in x_cat]
            y = y.to(self.device)
            
            self.optimizer.zero_grad()
            logits, _ = self.model(x_num, x_cat)
            # 替换损失函数：MSELoss → SmoothL1Loss
            loss = nn.SmoothL1Loss()(logits.squeeze(), y)  # 核心修改4
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
        
        return total_loss / len(dataloader)
    
    def evaluate(self, dataloader, test_df, categorical_cols, cat_encoder):
        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_labels = []
        all_disciplines = []
        
        with torch.no_grad():
            for i, batch in enumerate(dataloader):
                x_num, x_cat, y = batch
                x_num = x_num.to(self.device)
                x_cat = [cat.to(self.device) for cat in x_cat]
                y = y.to(self.device)
                
                logits, _ = self.model(x_num, x_cat)
                all_preds.append(logits.cpu().numpy().squeeze())
                all_labels.append(y.cpu().numpy())
                
                # 提取学科（原有代码不变）
                batch_size = x_cat[0].shape[0]
                start_idx = i * dataloader.batch_size
                end_idx = start_idx + batch_size
                batch_disciplines = test_df.iloc[start_idx:end_idx]['ResearchFields'].values
                all_disciplines.extend(batch_disciplines)
                
                loss = nn.SmoothL1Loss()(logits.squeeze(), y)
                total_loss += loss.item()
        
        all_preds = np.concatenate(all_preds)
        all_labels = np.concatenate(all_labels)
        all_disciplines = np.array(all_disciplines)
        
        # 整体指标：计算MSE和MAE（删除MAPE）
        overall_mse = mean_squared_error(all_labels, all_preds)
        overall_mae = mean_absolute_error(all_labels, all_preds)  # 新增MAE计算（核心修改）
        
        # 按学科计算指标：同样替换为MAE
        discipline_metrics = {}
        for disc in np.unique(all_disciplines):
            mask = (all_disciplines == disc)
            disc_preds = all_preds[mask]
            disc_labels = all_labels[mask]
            if len(disc_labels) == 0:
                continue
            disc_mse = mean_squared_error(disc_labels, disc_preds)
            disc_mae = mean_absolute_error(disc_labels, disc_preds)  # 学科层面MAE（核心修改）
            discipline_metrics[disc] = (disc_mse, disc_mae)  # 存储MSE和MAE
        
        # 返回值更新：用MAE替代原来的MAPE
        return (total_loss / len(dataloader), 
                overall_mse, 
                overall_mae,  # 现在返回的是MAE
                discipline_metrics)


# 6. 特征重要性可视化（支持多特征）

def plot_feature_importance(importance_matrix, feature_names, top_k=10):
    # 设置中文字体（关键修改）
    plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]  # 支持中文的字体列表
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
    
    global_importance = importance_matrix.mean(axis=0)
    sorted_idx = np.argsort(global_importance)[::-1][:top_k]
    top_features = [feature_names[i] for i in sorted_idx]
    top_importance = global_importance[sorted_idx]
    
    plt.figure(figsize=(10, 6))
    plt.barh(top_features, top_importance)
    plt.xlabel('全局特征重要性（平均注意力权重）')
    plt.title(f'Top {top_k} 影响排名的特征')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig('multi_discipline_rank_importance.png')
    plt.close()
    print(f"多学科特征重要性图已保存为：multi_discipline_rank_importance.png")


# 7. 批量读取多学科数据并合并
def load_multi_discipline_data(folder_path):
    all_dfs = []
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"在 {folder_path} 中未找到CSV文件！")
    
    for file in csv_files:
        disc_name = os.path.basename(file).replace(".csv", "")
        # 关键修正：
        # 1. 跳过第一行说明信息（skiprows=1）
        # 2. 指定编码为latin-1（解决之前的Unicode错误）
        df = pd.read_csv(file, skiprows=1, encoding='latin-1')
        
        # 3. 将第一列（空列名）重命名为“排名”（因为第一列实际存储排名）
        # 获取当前表头，将第一个列名改为“排名”
        cols = df.columns.tolist()
        cols[0] = "排名"  # 第一列是空列名，改为“排名”
        df.columns = cols
        
        # 4. 添加学科列
        df['ResearchFields'] = disc_name
        
        # 5. 验证必要列（现在列名已匹配）
        required_cols = ['排名', 'Institutions', 'Countries/Regions', 
                         'Web of Science Documents', 'Cites', 'Cites/Paper', 'Top Papers']
        if not set(required_cols).issubset(df.columns):
            # 打印实际列名，方便调试
            print(f"文件 {file} 的实际列名：{df.columns.tolist()}")
            raise ValueError(f"文件 {file} 缺少必要列：{required_cols}")
        
        all_dfs.append(df)
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    print(f"合并成功，共 {len(combined_df)} 条记录")
    return combined_df


# 8. 多学科排名预测主流程
def run_multi_discipline_rank_prediction(combined_df, numerical_cols, categorical_cols, target_col, epochs=50, batch_size=32):
    # 1. 清洗目标变量（原有代码）
    print("清洗目标变量（排名列）...")
    combined_df[target_col] = pd.to_numeric(combined_df[target_col], errors='coerce')
    combined_df = combined_df.dropna(subset=[target_col])
    combined_df[target_col] = combined_df[target_col].astype(int)
    print(f"清洗后的数据量：{len(combined_df)} 条")
    
    # 新增：按学科归一化排名（核心修改）
    # 公式：(当前排名 - 学科内最小排名) / (学科内最大排名 - 学科内最小排名) → 映射到[0,1]
    # 在run_multi_discipline_rank_prediction函数中，修改归一化代码
    combined_df['排名归一化'] = combined_df.groupby('ResearchFields')[target_col].transform(
        lambda x: (x - x.min()) / (x.max() - x.min() + 1e-6) + 1e-6  # +1e-6确保最小值为0.000001
    )
    # 验证调整后的最小值（应>0）
    print("调整后归一化排名的最小值：", combined_df['排名归一化'].min())  # 应输出≈1e-6
    # 验证归一化是否有效（打印示例）
    print("归一化排名示例（前5行）：")
    print(combined_df[['ResearchFields', target_col, '排名归一化']].head())
    # 替换目标变量为归一化后的排名
    target_col = '排名归一化'
    
    # 2. 添加比例特征（原有代码）
    combined_df['Top Papers比例'] = combined_df['Top Papers'] / (combined_df['Web of Science Documents'] + 1)
    combined_df['引用密度'] = combined_df['Cites'] / (combined_df['Web of Science Documents'] + 1)
    print("已添加新特征：Top Papers比例、引用密度")
    
    # 3. 更新数值特征列表（原有代码）
    numerical_cols = [
        'Web of Science Documents', 'Cites', 'Cites/Paper', 'Top Papers',
        'Top Papers比例', '引用密度'
    ]
    
    # 4. 打乱数据（原有代码）
    combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)
    print("数据已随机打乱顺序")

    preprocessor = TabularPreprocessor(numerical_cols, categorical_cols)
    preprocessor.fit(combined_df)
    num_features, cat_features = preprocessor.transform(combined_df)
    targets = combined_df[target_col].values  # 目标：排名位置
    
    # 划分训练集和测试集（按7:3拆分，保持学科分布）
    # 注意：此处简化为随机拆分，若需保持学科比例可使用分层抽样
    split_results = train_test_split(
        num_features, *cat_features, targets, combined_df,  # 额外传入原始df用于按学科评估
        test_size=0.3, random_state=42
    )
    # 拆分结果：num_train, num_test, cat1_train, cat1_test, ..., y_train, y_test, train_df, test_df
    num_train, num_test = split_results[0], split_results[1]
    cat_train = split_results[2 : 2 + 2*len(cat_features) : 2]
    cat_test = split_results[3 : 2 + 2*len(cat_features) : 2]
    y_train, y_test = split_results[-4], split_results[-3]
    train_df, test_df = split_results[-2], split_results[-1]  # 原始df的训练/测试部分
    
    # 创建数据加载器
    train_dataset = TabularDataset(num_train, cat_train, y_train)
    test_dataset = TabularDataset(num_test, cat_test, y_test)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    
    # 初始化模型（修改参数，核心修改3）
    embed_dim = 8
    tabnet = TabNet(
        num_numerical=len(numerical_cols),
        cat_dims=preprocessor.cat_dims,
        embed_dim=embed_dim,
        n_d=16,  # 从32减小到16
        n_a=16,  # 从32减小到16
        n_steps=2,  # 从4减少到2
        gamma=1.3,
        output_dim=1,
        task='regression'
    )
    trainer = TabNetTrainer(tabnet)
    
    # 训练模型
    print("=== 训练多学科排名预测模型 ===")
    for epoch in range(epochs):
        train_loss = trainer.train_epoch(train_loader)
        # 接收返回值时，val_mape的位置现在是val_mae（变量重命名）
        val_loss, val_mse, val_mae, _ = trainer.evaluate(  # 用val_mae接收MAE结果
            test_loader, test_df, categorical_cols, preprocessor.cat_encoders
        )
        # 打印日志：替换MAPE为MAE（核心修改）
        print(f"Epoch {epoch+1}/{epochs} | 训练损失: {train_loss:.4f} | 测试损失: {val_loss:.4f} | "
              f"测试MSE: {val_mse:.4f} | 测试MAE: {val_mae:.6f}")  # 显示MAE，保留6位小数
    
    # 生成特征名称（包含学科嵌入特征）
    feature_names = []
    feature_names.extend(numerical_cols)  # 数值特征
    for col in categorical_cols:
        for i in range(embed_dim):
            feature_names.append(f"{col}_embed_{i}")  # 类别嵌入特征（含学科）
    
    # 特征重要性分析
    tabnet.eval()
    all_importance = []
    with torch.no_grad():
        for batch in test_loader:
            x_num, x_cat, _ = batch
            x_num = x_num.to(trainer.device)
            x_cat = [cat.to(trainer.device) for cat in x_cat]
            _, importance = tabnet(x_num, x_cat)
            all_importance.append(importance.cpu().numpy())
    importance_matrix = np.concatenate(all_importance)
    plot_feature_importance(importance_matrix, feature_names)
    
    # 输出按学科的评估结果
    _, _, _, discipline_metrics = trainer.evaluate(
        test_loader, test_df, categorical_cols, preprocessor.cat_encoders
    )
    # 输出按学科的评估结果（同步更新为MAE）
    print("\n=== 按学科评估结果 ===")
    for disc, (mse, mae) in discipline_metrics.items():  # 现在是(mse, mae)
        print(f"学科: {disc} | MSE: {mse:.4f} | MAE: {mae:.6f}")  # 显示学科MAE
    
    return tabnet


# 9. 运行入口
if __name__ == "__main__":
    # 多学科CSV文件所在文件夹路径（替换为你的文件夹路径）
    folder_path = "D:/database/第七次作业10245501424李萍/data"  # 推荐：斜杠“/”
    
    # 加载并合并多学科数据
    combined_df = load_multi_discipline_data(folder_path)
    
    # 定义特征和目标列（新增"ResearchFields"作为学科类别特征）
    numerical_cols = [
        'Web of Science Documents', 
        'Cites', 
        'Cites/Paper', 
        'Top Papers'
    ]
    categorical_cols = ['Countries/Regions', 'ResearchFields']  # 国家 + 学科
    target_col = '排名'
    
    # 运行多学科排名预测模型
    model = run_multi_discipline_rank_prediction(
        combined_df,
        numerical_cols,
        categorical_cols,
        target_col,
        epochs=100,  # 从50增至100
        batch_size=16
    )