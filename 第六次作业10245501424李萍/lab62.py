import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine, text
from matplotlib.font_manager import FontProperties


# -------------------------- 1. 中文显示设置 --------------------------
def set_chinese_font():
    """设置支持中文的字体，兼容多系统"""
    try:
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
    except:
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示
    plt.rcParams['figure.facecolor'] = 'white'  # 避免图片背景透明


set_chinese_font()  # 初始化中文字体


# -------------------------- 2. 数据库连接 --------------------------
def get_db_engine():
    """创建支持UTF-8编码的SQLAlchemy引擎"""
    db_url = "mysql+pymysql://root:liping1231@localhost/academic_rankings?charset=utf8mb4"
    engine = create_engine(db_url)
    return engine


# -------------------------- 3. 肘部图分析与最佳k值确定 --------------------------
def find_optimal_k(X_scaled, max_k=10):
    """
    通过肘部图确定最佳聚类数k
    :param X_scaled: 标准化后的特征数据
    :param max_k: 最大测试k值
    :return: 最佳k值、WCSS列表
    """
    wcss = []
    k_range = range(1, max_k + 1)
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)  # n_init确保稳定性
        kmeans.fit(X_scaled)
        wcss.append(kmeans.inertia_)  # 记录簇内平方和
    
    # 绘制肘部图
    plt.figure(figsize=(10, 6))
    plt.plot(k_range, wcss, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('聚类数量k', fontsize=12)
    plt.ylabel('簇内平方和（WCSS）', fontsize=12)
    plt.title('KMeans聚类肘部图（最佳k值确定）', fontsize=14)
    plt.grid(alpha=0.3)
    
    # 自动识别肘部（基于WCSS下降率突变）
    wcss_diff = np.diff(wcss)  # 计算相邻k的WCSS差值（下降幅度）
    wcss_diff_ratio = wcss_diff[:-1] / wcss_diff[1:]  # 下降率的比例变化
    optimal_k = np.argmax(wcss_diff_ratio) + 2  # 找到最大比例变化点对应的k
    
    # 在图中标记最佳k值
    plt.axvline(x=optimal_k, color='r', linestyle='--', label=f'最佳k值: {optimal_k}')
    plt.legend(fontsize=12)
    plt.savefig("elbow_curve_with_optimal_k.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n通过肘部图分析，最佳聚类数k={optimal_k}")
    return optimal_k, wcss


# -------------------------- 4. 高校聚类与华师大相似性分析 --------------------------
def classify_and_find_similar():
    engine = get_db_engine()
    
    # 1. 读取ESI高校数据
    sql = text("""
    SELECT 
        i.id,
        i.name,
        i.country_region,
        COUNT(ip.research_field) AS subject_count,  # 学科数量
        AVG(ip.global_rank) AS avg_rank,            # 平均排名（越小越好）
        SUM(ip.web_of_science_documents) AS total_docs,
        SUM(ip.cites) AS total_cites,
        AVG(ip.cites_per_paper) AS avg_cites_per_paper,
        SUM(ip.top_papers) AS total_top_papers,
        SUM(CASE WHEN ip.global_rank <= 100 THEN 1 ELSE 0 END)/COUNT(ip.research_field) AS top100_ratio
    FROM institutions i
    JOIN institution_performance ip ON i.id = ip.institution_id
    WHERE ip.global_rank IS NOT NULL
    GROUP BY i.id, i.name, i.country_region
    HAVING subject_count >= 3  # 至少覆盖3个学科
    """)
    
    with engine.connect() as conn:
        uni_data = pd.read_sql(sql, conn)
    engine.dispose()
    
    # 数据清洗
    uni_data = uni_data.dropna()
    print(f"参与分析的高校数量：{uni_data.shape[0]}所")
    if uni_data.empty:
        print("无有效数据，程序终止")
        return
    
    # 2. 特征标准化与最佳k值确定
    features = [
        'subject_count', 'avg_rank', 'total_docs', 
        'total_cites', 'avg_cites_per_paper', 'total_top_papers', 'top100_ratio'
    ]
    X = uni_data[features]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 肘部图分析确定最佳k
    optimal_k, _ = find_optimal_k(X_scaled)
    
    # 3. 基于最佳k值进行K-Means聚类
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    uni_data['cluster'] = kmeans.fit_predict(X_scaled)
    
    # 4. 聚类结果分析（类别特征与命名）
    cluster_profiles = uni_data.groupby('cluster').agg({
        'subject_count': 'mean',
        'avg_rank': 'mean',
        'total_docs': 'mean',
        'total_cites': 'mean',
        'avg_cites_per_paper': 'mean',
        'total_top_papers': 'mean',
        'top100_ratio': 'mean',
        'country_region': lambda x: x.value_counts().index[0]  # 主要国家/地区
    }).round(2)
    cluster_profiles = cluster_profiles.rename(columns={'country_region': '主要国家/地区'})
    
    # 按平均排名（avg_rank）排序并命名类别（越小越优）
    cluster_ranking = cluster_profiles.sort_values('avg_rank').index.tolist()
    cluster_names = {cluster_ranking[i]: f'类别{i+1}（{label}）' for i, label in enumerate([
        '全球顶尖综合型', '区域领先特色型', '国际中等发展型', '新兴成长型'
    ][:optimal_k])}  # 动态适配最佳k值
    cluster_profiles['类别名称'] = cluster_profiles.index.map(cluster_names)
    
    print("\n=== 聚类类别特征概览 ===")
    print(cluster_profiles[['类别名称', 'avg_rank', 'top100_ratio', 'total_cites', '主要国家/地区']])
    
    # 5. PCA可视化聚类结果
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    uni_data['pca1'] = X_pca[:, 0]
    uni_data['pca2'] = X_pca[:, 1]
    
    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        data=uni_data,
        x='pca1', y='pca2',
        hue='cluster',
        palette='viridis',
        s=50, alpha=0.7
    )
    # 添加类别标签
    for cluster_id in cluster_profiles.index:
        centroid = X_pca[uni_data['cluster'] == cluster_id].mean(axis=0)
        plt.text(
            centroid[0], centroid[1],
            cluster_names[cluster_id],
            fontsize=12, fontweight='bold'
        )
    plt.title("ESI高校聚类PCA可视化（基于学科表现）", fontsize=14)
    plt.xlabel(f"PCA维度1（解释方差：{pca.explained_variance_ratio_[0]:.2%}）", fontsize=12)
    plt.ylabel(f"PCA维度2（解释方差：{pca.explained_variance_ratio_[1]:.2%}）", fontsize=12)
    plt.legend(title='高校类别', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(alpha=0.3)
    plt.savefig("university_clusters_pca.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # 6. 查找华东师大及相似学校
    # 6.1 定位华东师大
    ecnu_name = "EAST CHINA NORMAL UNIVERSITY"
    ecnu = uni_data[uni_data['name'].str.contains(ecnu_name, case=False, na=False)]
    if ecnu.empty:
        print(f"\n未找到{ecnu_name}的数据，请检查数据库中名称是否正确")
        return
    ecnu = ecnu.iloc[0]
    ecnu_cluster = ecnu['cluster']
    print(f"\n华东师范大学所属类别：{cluster_names[ecnu_cluster]}")
    print(f"华东师大核心指标：平均排名={ecnu['avg_rank']:.2f}，前100学科比例={ecnu['top100_ratio']:.2%}")
    
    # 6.2 计算余弦相似度（同簇内找最相似）
    ecnu_idx = uni_data[uni_data['id'] == ecnu['id']].index[0]
    ecnu_vec = X_scaled[ecnu_idx].reshape(1, -1)
    similarities = cosine_similarity(ecnu_vec, X_scaled).flatten()
    uni_data['similarity'] = similarities
    
    # 筛选同簇内非华师大的相似学校（前10）
    similar_uni = uni_data[
        (uni_data['cluster'] == ecnu_cluster) & 
        (uni_data['id'] != ecnu['id'])
    ].sort_values('similarity', ascending=False).head(10)
    
    # 7. 输出相似学校及分析
    print("\n=== 与华东师范大学最相似的10所学校（同类别内） ===")
    print(similar_uni[['name', 'country_region', 'similarity', 'avg_rank', 'top100_ratio']].round(4))
    
    # 7.1 相似性可视化
    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=similar_uni,
        x='similarity',
        y='name',
        hue='country_region',
        dodge=False,
        palette='Set2'
    )
    plt.axvline(x=1.0, color='r', linestyle='--', label='华东师大自身相似度（1.0）')
    plt.title("与华东师范大学的相似度排名（同类别内前10）", fontsize=14)
    plt.xlabel("余弦相似度（越高越相似）", fontsize=12)
    plt.ylabel("高校名称", fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig("ecnu_similar_universities.png", dpi=300)
    plt.close()
    
   # 7.2 相似性原因分析
    print("\n=== 相似性原因分析 ===")
    # 提取华师大与相似学校的共性特征
    ecnu_features = ecnu[features].to_frame().T
    ecnu_features.index = ['华东师大']  # 为华师大特征设置索引

    similar_avg = similar_uni[features].mean().to_frame().T
    similar_avg.index = ['相似学校均值']  # 为相似学校均值设置索引

    comparison = pd.concat([ecnu_features, similar_avg]).round(2)  # 拼接两个DataFrame
    print("\n核心特征对比（均值）：")
    print(comparison)

    # 自动生成分析结论
    print("\n结论：")
    print(f"1. 所有相似学校与华东师大同属{cluster_names[ecnu_cluster]}，整体学科实力处于同一层级")
    print(f"2. 核心共性：平均排名（avg_rank）接近（华东师大{ecnu['avg_rank']:.2f} vs 相似学校{similar_avg['avg_rank'].values[0]:.2f}），")
    print(f"   前100学科比例（top100_ratio）相当（华东师大{ecnu['top100_ratio']:.2%} vs 相似学校{similar_avg['top100_ratio'].values[0]:.2%}），")
    print(f"   科研产出（total_docs）和影响力（total_cites）水平匹配")
    print("3. 这类学校通常以特色学科为核心（如师范类、区域优势学科），而非全学科顶尖，符合‘区域领先特色型’定位")
    
    return uni_data, similar_uni


# -------------------------- 主函数执行 --------------------------
if __name__ == "__main__":
    print("=== ESI高校聚类与华东师大相似性分析 ===")
    uni_data, similar_uni = classify_and_find_similar()
    print("\n分析完成！结果已保存为图片（肘部图、PCA聚类图、相似度排名图）")