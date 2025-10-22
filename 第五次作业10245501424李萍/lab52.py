import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
# 关键：导入SQLAlchemy的text对象，处理中文SQL
from sqlalchemy import create_engine, text
# 新增：检查系统字体（可选，用于调试）
from matplotlib.font_manager import FontProperties


# -------------------------- 1. 修复中文显示问题 --------------------------
def set_chinese_font():
    """设置支持中文的字体，兼容多系统"""
    try:
        # 优先尝试Windows默认中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
    except:
        #  Linux/macOS备选字体
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示
    plt.rcParams['figure.facecolor'] = 'white'  # 避免图片背景透明


# 初始化中文字体（必须在绘图前调用）
set_chinese_font()


# -------------------------- 2. 修复数据库连接与SQL编码 --------------------------
def get_db_engine():
    """创建支持UTF-8编码的SQLAlchemy引擎，解决中文查询错误"""
    # 关键：添加charset=utf8mb4，确保中文编码正确
    db_url = "mysql+pymysql://root:liping1231@localhost/academic_rankings?charset=utf8mb4"
    engine = create_engine(db_url)
    return engine


# -------------------------- 3. 修复高校分类逻辑（类别命名颠倒） --------------------------
def classify_global_universities():
    engine = get_db_engine()
    
    # 1. 读取高校综合数据（SQL不变，用text包裹避免编码问题）
    sql = text("""
    SELECT 
        i.id,
        i.name,
        i.country_region,
        COUNT(ip.research_field) AS subject_count,  # 学科数量
        AVG(ip.global_rank) AS avg_rank,            # 平均排名（越小越好！）
        SUM(ip.web_of_science_documents) AS total_docs,
        SUM(ip.cites) AS total_cites,
        AVG(ip.cites_per_paper) AS avg_cites_per_paper,
        SUM(ip.top_papers) AS total_top_papers,
        SUM(CASE WHEN ip.global_rank <= 100 THEN 1 ELSE 0 END)/COUNT(ip.research_field) AS top100_ratio
    FROM institutions i
    JOIN institution_performance ip ON i.id = ip.institution_id
    WHERE ip.global_rank IS NOT NULL
    GROUP BY i.id, i.name, i.country_region
    HAVING subject_count >= 3  # 放宽条件，让分类更均匀（原5→3）
    """)
    # 用engine.execute+text处理SQL，避免中文编码错误
    with engine.connect() as conn:
        uni_data = pd.read_sql(sql, conn)
    engine.dispose()
    
    # 数据清洗
    uni_data = uni_data.dropna()
    print(f"参与分类的高校数量：{uni_data.shape[0]}所")
    
    # 2. 聚类特征与标准化
    features = [
        'subject_count', 'avg_rank', 'total_docs', 
        'total_cites', 'avg_cites_per_paper', 'total_top_papers', 'top100_ratio'
    ]
    X = uni_data[features]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 3. K-Means聚类（K=4，调整后分布更均匀）
    k = 4
    kmeans = KMeans(n_clusters=k, random_state=42)
    uni_data['cluster'] = kmeans.fit_predict(X_scaled)
    
    # 4. 查看分类分布（修正后更均匀）
    cluster_dist = uni_data['cluster'].value_counts().sort_index()
    print("\n高校分类分布：")
    print(cluster_dist)
    
    # 5. 分析类别特征（关键：按avg_rank排序，确定正确类别名称）
    cluster_profiles = uni_data.groupby('cluster').agg({
        'subject_count': 'mean',
        'avg_rank': 'mean',          # 核心指标：越小排名越优
        'total_docs': 'mean',
        'total_cites': 'mean',
        'avg_cites_per_paper': 'mean',
        'total_top_papers': 'mean',
        'top100_ratio': 'mean',
        'country_region': lambda x: x.value_counts().index[0]  # 主要国家
    }).round(2)
    # 重命名列，避免KeyError
    cluster_profiles = cluster_profiles.rename(columns={'country_region': '主要国家'})
    
    # 6. 修正类别命名（按avg_rank从小到大：顶尖→新兴）
    # 先按avg_rank排序，确定每个cluster的等级
    cluster_ranking = cluster_profiles.sort_values('avg_rank').index.tolist()
    cluster_names = {
        cluster_ranking[0]: "全球顶尖综合型",  # avg_rank最小（排名最优）
        cluster_ranking[1]: "区域领先特色型",  # avg_rank次之
        cluster_ranking[2]: "国际中等发展型",  # avg_rank中等
        cluster_ranking[3]: "新兴成长型"        # avg_rank最大（排名最差）
    }
    cluster_profiles['类别名称'] = cluster_profiles.index.map(cluster_names)
    
    # 打印修正后的类别特征（逻辑正确）
    print("\n各类别特征概览（avg_rank越小排名越优）：")
    print(cluster_profiles[['类别名称', 'avg_rank', 'top100_ratio', 'total_cites', '主要国家']])
    
    # 7. PCA可视化（中文正常显示）
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
        s=50, alpha=0.7,
        hue_order=cluster_profiles.index
    )
    # 添加类别标签（中文正常显示）
    for cluster_id in cluster_profiles.index:
        centroid = X_pca[uni_data['cluster'] == cluster_id].mean(axis=0)
        plt.text(
            centroid[0], centroid[1], 
            cluster_names[cluster_id],  # 正确的类别名称
            fontsize=12, fontweight='bold'
        )
    plt.title("全球高校分类PCA可视化（基于学科综合表现）")
    plt.xlabel(f"PCA维度1（解释方差：{pca.explained_variance_ratio_[0]:.2%}）")
    plt.ylabel(f"PCA维度2（解释方差：{pca.explained_variance_ratio_[1]:.2%}）")
    plt.legend(title='高校类别')
    plt.grid(alpha=0.3)
    plt.savefig("university_clusters_fixed.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    return uni_data, cluster_profiles


# -------------------------- 4. 修复华东师大相似高校查询（SQL编码问题） --------------------------
def find_similar_to_ecnu(uni_data):
    engine = get_db_engine()
    
    # 关键：用text包裹SQL，避免中文编码被解析为格式符
    ecnu_sql = text("""
    SELECT id, name, country_region 
    FROM institutions 
    WHERE name LIKE :name_pattern  # 用参数化查询，彻底避免编码问题
    """)
    
    # 用参数化传入中文关键词，而非直接拼接SQL
    with engine.connect() as conn:
        # 传入参数：%华东师范大学%（通配符正确拼接）
        ecnu_df = pd.read_sql(ecnu_sql, conn, params={"name_pattern": "%EAST CHINA NORMAL UNIVERSITY%"})
    
    engine.dispose()
    
    # 检查是否找到华东师大
    if ecnu_df.empty:
        print("\n未找到华东师范大学！请检查数据库中机构名称是否为‘华东师范大学’（无空格/特殊字符）")
        return None
    
    ecnu = ecnu_df.iloc[0]
    ecnu_id = ecnu['id']
    print(f"\n找到华东师范大学：{ecnu['name']}（国家/地区：{ecnu['country_region']}）")
    
    # 计算余弦相似度（逻辑不变）
    features = [
        'subject_count', 'avg_rank', 'total_docs', 
        'total_cites', 'avg_cites_per_paper', 'total_top_papers', 'top100_ratio'
    ]
    X = uni_data[features]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 华东师大的特征向量
    ecnu_idx = uni_data[uni_data['id'] == ecnu_id].index[0]
    ecnu_vec = X_scaled[ecnu_idx].reshape(1, -1)
    
    # 计算相似度
    similarities = cosine_similarity(ecnu_vec, X_scaled).flatten()
    uni_data['similarity'] = similarities
    
    # 筛选前10相似高校
    similar_uni = uni_data[uni_data['id'] != ecnu_id].sort_values('similarity', ascending=False).head(10)
    similar_uni = similar_uni[['name', 'country_region', 'similarity', 'avg_rank', 'top100_ratio', 'subject_count']]
    similar_uni['similarity'] = similar_uni['similarity'].round(4)
    
    print("\n与华东师范大学最相似的10所高校：")
    print(similar_uni)
    
    # 可视化（中文正常显示）
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
    plt.title("与华东师范大学的相似度排名（前10）")
    plt.xlabel("余弦相似度（越高越相似）")
    plt.ylabel("高校名称")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig("ecnu_similar_unis_fixed.png", dpi=300)
    plt.close()
    
    return similar_uni


# -------------------------- 5. 华东师大科目画像（复用修复的SQL逻辑） --------------------------
def ecnu_subject_profile():
    engine = get_db_engine()
    
    # 1. 读取华东师大科目数据（参数化查询）
    ecnu_subj_sql = text("""
    SELECT 
        ip.research_field,
        ip.global_rank,
        ip.web_of_science_documents AS docs,
        ip.cites,
        ip.cites_per_paper,
        ip.top_papers
    FROM institution_performance ip
    JOIN institutions i ON ip.institution_id = i.id
    WHERE i.name LIKE :name_pattern AND ip.global_rank IS NOT NULL
    """)
    
    with engine.connect() as conn:
        ecnu_subjects = pd.read_sql(ecnu_subj_sql, conn, params={"name_pattern": "%EAST CHINA NORMAL UNIVERSITY%"})
    
    # 2. 读取全球平均数据
    global_avg_sql = text("""
    SELECT 
        research_field,
        AVG(global_rank) AS avg_global_rank,
        AVG(web_of_science_documents) AS avg_docs,
        AVG(cites) AS avg_cites,
        AVG(cites_per_paper) AS avg_cites_per_paper,
        AVG(top_papers) AS avg_top_papers
    FROM institution_performance
    WHERE global_rank IS NOT NULL
    GROUP BY research_field
    """)
    
    with engine.connect() as conn:
        global_avg = pd.read_sql(global_avg_sql, conn)
    
    engine.dispose()
    
    if ecnu_subjects.empty:
        print("\n未找到华东师范大学的科目数据！")
        return None
    
    # 3. 科目画像统计
    total_subjects = ecnu_subjects.shape[0]
    top50_subjects = ecnu_subjects[ecnu_subjects['global_rank'] <= 50].shape[0]
    top100_subjects = ecnu_subjects[ecnu_subjects['global_rank'] <= 100].shape[0]
    
    print(f"\n=== 华东师范大学学科画像 ===")
    print(f"学科覆盖总数：{total_subjects}个")
    print(f"全球前50学科：{top50_subjects}个（占比{top50_subjects/total_subjects:.2%}）")
    print(f"全球前100学科：{top100_subjects}个（占比{top100_subjects/total_subjects:.2%}）")
    
    # 4. 优势/短板学科
    top_subjects = ecnu_subjects.sort_values('global_rank').head(10)
    weak_subjects = ecnu_subjects.sort_values('global_rank', ascending=False).head(10)
    
    print("\n优势学科（全球排名前10）：")
    print(top_subjects[['research_field', 'global_rank', 'cites_per_paper']])
    print("\n短板学科（全球排名靠后）：")
    print(weak_subjects[['research_field', 'global_rank', 'cites_per_paper']])
    
    # 5. 优势学科可视化（中文正常显示）
    plt.figure(figsize=(12, 6))
    sns.barplot(
        data=top_subjects,
        x='research_field',
        y='global_rank',
        palette='Greens_d'
    )
    plt.axhline(y=50, color='orange', linestyle='--', label='全球前50线')
    plt.axhline(y=100, color='red', linestyle='--', label='全球前100线')
    plt.title("华东师范大学优势学科全球排名")
    plt.ylabel("全球排名（数值越小越好）")
    plt.xlabel("学科领域")
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig("ecnu_top_subjects_fixed.png", dpi=300)
    plt.close()
    
    return ecnu_subjects


# -------------------------- 主函数（执行所有功能） --------------------------
if __name__ == "__main__":
    # 功能1：全球高校分类（修复后逻辑正确、中文正常）
    uni_data, cluster_profiles = classify_global_universities()
    
    # 功能2：查找相似高校（修复SQL编码问题）
    if not uni_data.empty:
        similar_unis = find_similar_to_ecnu(uni_data)
    
    # 功能3：华东师大科目画像
    ecnu_profile = ecnu_subject_profile()
    
    print("\n所有分析完成！修复后的图片已保存（文件名含fixed后缀）。")