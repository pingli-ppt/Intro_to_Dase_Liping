# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
# import os
# import glob
# import re

# # 设置中文字体
# plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
# plt.rcParams['axes.unicode_minus'] = False

# # 华东师范大学各专业数据
# ecnu_major_data = {
#     '专业': ['CHEMISTRY', 'MATHEMATICS', 'ENVIRONMENT/ECOLOGY', 'MATERIALS SCIENCE', 
#             'COMPUTER SCIENCE', 'GEOSCIENCES', 'ENGINEERING', 'PLANT & ANIMAL SCIENCE',
#             'PSYCHIATRY/PSYCHOLOGY', 'PHYSICS', 'BIOLOGY & BIOCHEMISTRY', 
#             'AGRICULTURAL SCIENCES', 'NEUROSCIENCE & BEHAVIOR', 
#             'MOLECULAR BIOLOGY & GENETICS', 'PHARMACOLOGY & TOXICOLOGY', 'CLINICAL MEDICINE'],
#     '排名': [90, 115, 130, 196, 207, 275, 317, 395, 467, 522, 721, 845, 853, 867, 1064, 2852],
#     '总学校数': [2141, 395, 2066, 1580, 863, 1175, 2787, 1950, 1147, 995, 1649, 1381, 1298, 1169, 1389, 6754],
#     '论文数': [5420, 2019, 2941, 2720, 1803, 1850, 2567, 1375, 1460, 3495, 897, 346, 771, 532, 289, 940],
#     '引用次数': [164390, 11984, 92088, 93969, 22336, 42158, 55450, 21843, 15243, 50802, 20837, 6513, 14295, 20568, 5693, 16875],
#     '平均引用次数': [30.33, 5.94, 31.31, 34.55, 12.39, 22.79, 21.60, 15.89, 10.44, 14.54, 23.23, 18.82, 18.54, 38.66, 19.70, 17.95]
# }

# # 获取当前脚本所在目录
# current_dir = os.path.dirname(os.path.abspath(__file__))
# data_dir = os.path.join(current_dir, "esi_institution_rankings")
# output_dir = current_dir

# def create_major_data_table():
#     """创建专业数据表格可视化"""
#     df = pd.DataFrame(ecnu_major_data)
    
#     # 计算额外指标
#     df['前百分比'] = (df['排名'] / df['总学校数'] * 100).round(2)
#     df['论文影响力'] = (df['平均引用次数'] / df['平均引用次数'].max() * 100).round(2)
    
#     # 1. 专业排名热力图
#     plt.figure(figsize=(14, 10))
    
#     # 准备热力图数据
#     heatmap_data = df[['排名', '论文数', '引用次数', '平均引用次数', '前百分比']].copy()
#     heatmap_data.index = df['专业']
    
#     # 标准化数据（排名和百分比需要反向处理，因为数值越小越好）
#     normalized_data = heatmap_data.copy()
#     for col in ['排名', '前百分比']:
#         normalized_data[col] = 1 - (normalized_data[col] / normalized_data[col].max())
#     for col in ['论文数', '引用次数', '平均引用次数']:
#         normalized_data[col] = normalized_data[col] / normalized_data[col].max()
    
#     plt.imshow(normalized_data.T, cmap='YlGnBu', aspect='auto')
#     plt.colorbar(label='标准化值 (越高越好)')
#     plt.xticks(range(len(df)), df['专业'], rotation=45, ha='right')
#     plt.yticks(range(len(normalized_data.columns)), normalized_data.columns)
#     plt.title('华东师范大学各专业ESI指标热力图', fontsize=16, fontweight='bold', pad=20)
    
#     # 添加数值标注
#     for i in range(len(normalized_data.columns)):
#         for j in range(len(normalized_data)):
#             plt.text(j, i, f'{heatmap_data.iloc[j, i]:.0f}', 
#                     ha='center', va='center', fontsize=8, fontweight='bold',
#                     color='white' if normalized_data.iloc[j, i] > 0.5 else 'black')
    
#     plt.tight_layout()
#     heatmap_path = os.path.join(output_dir, 'major_heatmap.png')
#     plt.savefig(heatmap_path, dpi=300, bbox_inches='tight', facecolor='white')
#     plt.close()
    
#     # 2. 专业排名条形图
#     plt.figure(figsize=(14, 10))
#     df_sorted = df.sort_values('排名')
    
#     colors = []
#     for rank in df_sorted['排名']:
#         if rank <= 100:
#             colors.append('#FF6B6B')  # 红色 - 顶尖
#         elif rank <= 200:
#             colors.append('#4ECDC4')  # 绿色 - 优秀
#         elif rank <= 500:
#             colors.append('#45B7D1')  # 蓝色 - 良好
#         else:
#             colors.append('#96CEB4')  # 浅绿 - 一般
    
#     bars = plt.barh(range(len(df_sorted)), df_sorted['排名'], color=colors, alpha=0.8)
#     plt.yticks(range(len(df_sorted)), df_sorted['专业'], fontsize=11)
#     plt.title('华东师范大学各专业ESI全球排名', fontsize=16, fontweight='bold', pad=20)
#     plt.xlabel('全球排名 (数字越小越好)', fontsize=12)
#     plt.gca().invert_yaxis()
#     plt.grid(axis='x', alpha=0.3)
    
#     # 添加排名数值标签
#     for i, (bar, rank) in enumerate(zip(bars, df_sorted['排名'])):
#         plt.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2, 
#                 f'第{int(rank)}名', ha='left', va='center', fontweight='bold', fontsize=10)
    
#     # 添加图例
#     from matplotlib.patches import Patch
#     legend_elements = [
#         Patch(facecolor='#FF6B6B', label='顶尖 (前100)', alpha=0.8),
#         Patch(facecolor='#4ECDC4', label='优秀 (101-200)', alpha=0.8),
#         Patch(facecolor='#45B7D1', label='良好 (201-500)', alpha=0.8),
#         Patch(facecolor='#96CEB4', label='一般 (500+)', alpha=0.8)
#     ]
#     plt.legend(handles=legend_elements, loc='lower right', fontsize=10)
    
#     plt.tight_layout()
#     bar_path = os.path.join(output_dir, 'major_ranking.png')
#     plt.savefig(bar_path, dpi=300, bbox_inches='tight', facecolor='white')
#     plt.close()
    
#     # 3. 论文影响力散点图
#     plt.figure(figsize=(12, 8))
#     scatter = plt.scatter(df['论文数'], df['平均引用次数'], 
#                          s=df['引用次数']/100, alpha=0.7, 
#                          c=df['排名'], cmap='viridis_r')
    
#     plt.colorbar(scatter, label='全球排名 (颜色越深排名越好)')
#     plt.xlabel('论文数量', fontsize=12)
#     plt.ylabel('平均引用次数', fontsize=12)
#     plt.title('华东师范大学各专业科研产出与影响力', fontsize=14, fontweight='bold')
#     plt.grid(alpha=0.3)
    
#     # 添加专业标签
#     for i, major in enumerate(df['专业']):
#         plt.annotate(major.split('/')[0].split('&')[0], 
#                     (df['论文数'].iloc[i], df['平均引用次数'].iloc[i]),
#                     xytext=(5, 5), textcoords='offset points', fontsize=8)
    
#     plt.tight_layout()
#     scatter_path = os.path.join(output_dir, 'major_scatter.png')
#     plt.savefig(scatter_path, dpi=300, bbox_inches='tight', facecolor='white')
#     plt.close()
    
#     return {
#         '专业数据热力图': 'major_heatmap.png',
#         '专业排名分布': 'major_ranking.png',
#         '科研产出影响力': 'major_scatter.png'
#     }, df

# def generate_major_data_report(charts, major_df):
#     """生成专业数据的HTML报告"""
    
#     # 计算统计指标
#     total_majors = len(major_df)
#     top_100 = len(major_df[major_df['排名'] <= 100])
#     top_200 = len(major_df[major_df['排名'] <= 200])
#     top_500 = len(major_df[major_df['排名'] <= 500])
#     avg_rank = major_df['排名'].mean()
#     best_rank = major_df['排名'].min()
#     best_major = major_df.loc[major_df['排名'].idxmin(), '专业']
#     highest_citation = major_df.loc[major_df['平均引用次数'].idxmax(), '专业']
#     highest_avg_citation = major_df['平均引用次数'].max()
    
#     html_content = f"""
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <meta charset="UTF-8">
#         <title>华东师范大学各专业ESI数据分析报告</title>
#         <style>
#             body {{ font-family: Arial, sans-serif; margin: 30px; line-height: 1.6; background-color: #f8f9fa; }}
#             .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
#             h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 15px; }}
#             h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 15px; margin-top: 30px; }}
#             .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
#             .metric-box {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-top: 4px solid #3498db; }}
#             .metric-value {{ font-size: 2.2em; font-weight: bold; color: #3498db; margin: 10px 0; }}
#             table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
#             th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
#             th {{ background-color: #3498db; color: white; }}
#             tr:nth-child(even) {{ background-color: #f8f9fa; }}
#             .top-100 {{ background-color: #fff3cd; }}
#             .top-200 {{ background-color: #e2e3e5; }}
#             .chart {{ text-align: center; margin: 30px 0; padding: 20px; background: white; border-radius: 8px; }}
#             .summary {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 25px; border-radius: 8px; margin: 20px 0; }}
#             .footer {{ text-align: center; margin-top: 40px; color: #666; padding-top: 20px; border-top: 1px solid #ddd; }}
#             .major-name {{ font-weight: bold; color: #2c3e50; }}
#             .highlight {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
#         </style>
#     </head>
#     <body>
#         <div class="container">
#             <h1>📊 华东师范大学各专业ESI数据分析报告</h1>
            
#             <div class="summary">
#                 <h2>🎯 核心发现</h2>
#                 <p>基于华东师范大学16个ESI学科的详细数据，分析各专业在全球的学术表现、科研产出和影响力。</p>
#                 <p>涵盖了排名、论文数量、引用次数等关键指标的综合分析。</p>
#             </div>

#             <div class="metrics">
#                 <div class="metric-box">
#                     <div class="metric-value">{total_majors}</div>
#                     <div>分析专业总数</div>
#                 </div>
#                 <div class="metric-box">
#                     <div class="metric-value">{best_rank}</div>
#                     <div>最佳全球排名</div>
#                 </div>
#                 <div class="metric-box">
#                     <div class="metric-value">{avg_rank:.0f}</div>
#                     <div>平均全球排名</div>
#                 </div>
#                 <div class="metric-box">
#                     <div class="metric-value">{top_100}</div>
#                     <div>顶尖学科(前100)</div>
#                 </div>
#             </div>
            
#             <div class="highlight">
#                 <h3>🏆 亮点专业</h3>
#                 <p><strong>排名最佳专业</strong>: {best_major} (全球第{best_rank}名)</p>
#                 <p><strong>论文影响力最高</strong>: {highest_citation} (平均引用{highest_avg_citation}次)</p>
#                 <p><strong>科研产出最多</strong>: {major_df.loc[major_df['论文数'].idxmax(), '专业']} (共{major_df['论文数'].max()}篇论文)</p>
#             </div>
            
#             <h2>📋 各专业详细数据表</h2>
#             <table>
#                 <tr>
#                     <th>专业名称</th>
#                     <th>全球排名</th>
#                     <th>总学校数</th>
#                     <th>论文数量</th>
#                     <th>引用次数</th>
#                     <th>平均引用</th>
#                     <th>全球前百分比</th>
#                     <th>水平评估</th>
#                 </tr>
#     """
    
#     # 添加表格行
#     for _, row in major_df.sort_values('排名').iterrows():
#         rank = row['排名']
#         total_schools = row['总学校数']
#         papers = row['论文数']
#         citations = row['引用次数']
#         avg_citation = row['平均引用次数']
#         percentile = round(rank / total_schools * 100, 2)  # 修复这里：使用round函数而不是方法
        
#         if rank <= 100:
#             level = "⭐ 顶尖学科"
#             row_class = "top-100"
#         elif rank <= 200:
#             level = "🔶 优秀学科"
#             row_class = "top-200"
#         elif rank <= 500:
#             level = "📊 良好学科"
#             row_class = ""
#         else:
#             level = "🌍 一般学科"
#             row_class = ""
        
#         html_content += f"""
#                 <tr class="{row_class}">
#                     <td class="major-name">{row['专业']}</td>
#                     <td><strong>第{rank}名</strong></td>
#                     <td>{total_schools}</td>
#                     <td>{papers}</td>
#                     <td>{citations}</td>
#                     <td>{avg_citation}</td>
#                     <td>前{percentile}%</td>
#                     <td>{level}</td>
#                 </tr>
#         """
    
#     html_content += """
#             </table>
            
#             <h2>📈 专业数据可视化分析</h2>
#     """
    
#     # 添加图表
#     for chart_name, chart_file in charts.items():
#         html_content += f"""
#             <div class="chart">
#                 <h3>{chart_name}</h3>
#                 <img src="{chart_file}" alt="{chart_name}" style="max-width: 95%; border-radius: 5px;">
#             </div>
#         """
    
#     # 添加数据洞察
#     html_content += """
#             <div style="background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
#                 <h2>💡 数据洞察</h2>
#                 <h3>优势领域:</h3>
#                 <ul>
#                     <li>化学、数学、环境/生态学等专业进入全球前150名，表现突出</li>
#                     <li>材料科学平均引用次数高达34.55，论文影响力显著</li>
#                     <li>多个专业在各自领域的全球竞争力强劲</li>
#                 </ul>
                
#                 <h3>改进机会:</h3>
#                 <ul>
#                     <li>临床医学等专业排名相对靠后，有提升空间</li>
#                     <li>部分专业论文数量相对较少，可加强科研产出</li>
#                     <li>数学等基础学科平均引用次数较低，需提升论文影响力</li>
#                 </ul>
#             </div>
            
#             <div class="footer">
#                 <p>⏰ 报告生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
#                 <p>📚 数据来源: Clarivate ESI (Essential Science Indicators)</p>
#                 <p>💡 分析维度: 全球排名、论文产出、引用影响力等多维度评估</p>
#                 <p>💻 分析工具: Python数据分析与可视化</p>
#             </div>
#         </div>
#     </body>
#     </html>
#     """
    
#     report_path = os.path.join(output_dir, "华东师范大学_各专业ESI数据分析报告.html")
#     with open(report_path, "w", encoding="utf-8") as f:
#         f.write(html_content)
#     print(f"📄 专业数据HTML报告已生成: {report_path}")

# def main_with_major_data():
#     """主函数（包含专业数据）"""
#     print("🚀 开始华东师范大学专业ESI数据分析...")
    
#     # 创建专业数据可视化
#     print("📊 创建专业数据可视化...")
#     charts, major_df = create_major_data_table()
    
#     # 生成专业数据报告
#     print("📄 生成专业数据分析报告...")
#     generate_major_data_report(charts, major_df)
    
#     # 输出统计信息
#     print(f"\n✅ 专业数据分析完成！")
#     print(f"📊 分析了 {len(major_df)} 个专业的ESI数据")
#     print(f"🥇 最佳排名专业: {major_df.loc[major_df['排名'].idxmin(), '专业']} (第{major_df['排名'].min()}名)")
#     print(f"📈 最高影响力专业: {major_df.loc[major_df['平均引用次数'].idxmax(), '专业']} (平均引用{major_df['平均引用次数'].max()}次)")
#     print(f"📁 所有生成文件都保存在: {output_dir}")

# if __name__ == "__main__":
#     main_with_major_data()
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
import re
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 华东师范大学各专业数据（包含SOCIAL SCIENCES, GENERAL）
ecnu_major_data = {
    '专业': ['CHEMISTRY', 'MATHEMATICS', 'ENVIRONMENT/ECOLOGY', 'MATERIALS SCIENCE', 
            'COMPUTER SCIENCE', 'GEOSCIENCES', 'ENGINEERING', 'PLANT & ANIMAL SCIENCE',
            'PSYCHIATRY/PSYCHOLOGY', 'PHYSICS', 'BIOLOGY & BIOCHEMISTRY', 
            'AGRICULTURAL SCIENCES', 'NEUROSCIENCE & BEHAVIOR', 
            'MOLECULAR BIOLOGY & GENETICS', 'PHARMACOLOGY & TOXICOLOGY', 'CLINICAL MEDICINE',
            'SOCIAL SCIENCES, GENERAL'],
    '排名': [90, 115, 130, 196, 207, 275, 317, 395, 467, 522, 721, 845, 853, 867, 1064, 2852, 650],
    '总学校数': [2141, 395, 2066, 1580, 863, 1175, 2787, 1950, 1147, 995, 1649, 1381, 1298, 1169, 1389, 6754, 1888],
    '论文数': [5420, 2019, 2941, 2720, 1803, 1850, 2567, 1375, 1460, 3495, 897, 346, 771, 532, 289, 940, 1250],
    '引用次数': [164390, 11984, 92088, 93969, 22336, 42158, 55450, 21843, 15243, 50802, 20837, 6513, 14295, 20568, 5693, 16875, 15600],
    '平均引用次数': [30.33, 5.94, 31.31, 34.55, 12.39, 22.79, 21.60, 15.89, 10.44, 14.54, 23.23, 18.82, 18.54, 38.66, 19.70, 17.95, 12.48]
}

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, "esi_institution_rankings")
output_dir = current_dir

def create_major_data_table():
    """创建专业数据表格可视化"""
    df = pd.DataFrame(ecnu_major_data)
    
    # 计算额外指标
    df['前百分比'] = (df['排名'] / df['总学校数'] * 100).round(2)
    df['论文影响力'] = (df['平均引用次数'] / df['平均引用次数'].max() * 100).round(2)
    
    # 1. 专业排名热力图
    plt.figure(figsize=(16, 12))
    
    # 准备热力图数据
    heatmap_data = df[['排名', '论文数', '引用次数', '平均引用次数', '前百分比']].copy()
    heatmap_data.index = df['专业']
    
    # 标准化数据（排名和百分比需要反向处理，因为数值越小越好）
    normalized_data = heatmap_data.copy()
    for col in ['排名', '前百分比']:
        normalized_data[col] = 1 - (normalized_data[col] / normalized_data[col].max())
    for col in ['论文数', '引用次数', '平均引用次数']:
        normalized_data[col] = normalized_data[col] / normalized_data[col].max()
    
    plt.imshow(normalized_data.T, cmap='YlGnBu', aspect='auto')
    plt.colorbar(label='标准化值 (越高越好)')
    plt.xticks(range(len(df)), df['专业'], rotation=45, ha='right', fontsize=10)
    plt.yticks(range(len(normalized_data.columns)), normalized_data.columns, fontsize=11)
    plt.title('华东师范大学各专业ESI指标热力图', fontsize=16, fontweight='bold', pad=20)
    
    # 添加数值标注
    for i in range(len(normalized_data.columns)):
        for j in range(len(normalized_data)):
            value = heatmap_data.iloc[j, i]
            if col in ['平均引用次数', '前百分比']:
                text = f'{value:.1f}'
            else:
                text = f'{value:.0f}'
            plt.text(j, i, text, 
                    ha='center', va='center', fontsize=8, fontweight='bold',
                    color='white' if normalized_data.iloc[j, i] > 0.5 else 'black')
    
    plt.tight_layout()
    heatmap_path = os.path.join(output_dir, 'major_heatmap.png')
    plt.savefig(heatmap_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    # 2. 专业排名条形图
    plt.figure(figsize=(16, 12))
    df_sorted = df.sort_values('排名')
    
    colors = []
    for rank in df_sorted['排名']:
        if rank <= 100:
            colors.append('#FF6B6B')  # 红色 - 顶尖
        elif rank <= 200:
            colors.append('#4ECDC4')  # 绿色 - 优秀
        elif rank <= 500:
            colors.append('#45B7D1')  # 蓝色 - 良好
        else:
            colors.append('#96CEB4')  # 浅绿 - 一般
    
    bars = plt.barh(range(len(df_sorted)), df_sorted['排名'], color=colors, alpha=0.8)
    plt.yticks(range(len(df_sorted)), df_sorted['专业'], fontsize=11)
    plt.title('华东师范大学各专业ESI全球排名', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('全球排名 (数字越小越好)', fontsize=12)
    plt.gca().invert_yaxis()
    plt.grid(axis='x', alpha=0.3)
    
    # 添加排名数值标签
    for i, (bar, rank) in enumerate(zip(bars, df_sorted['排名'])):
        plt.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2, 
                f'第{int(rank)}名', ha='left', va='center', fontweight='bold', fontsize=10)
    
    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#FF6B6B', label='顶尖 (前100)', alpha=0.8),
        Patch(facecolor='#4ECDC4', label='优秀 (101-200)', alpha=0.8),
        Patch(facecolor='#45B7D1', label='良好 (201-500)', alpha=0.8),
        Patch(facecolor='#96CEB4', label='一般 (500+)', alpha=0.8)
    ]
    plt.legend(handles=legend_elements, loc='lower right', fontsize=10)
    
    plt.tight_layout()
    bar_path = os.path.join(output_dir, 'major_ranking.png')
    plt.savefig(bar_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    # 3. 论文影响力散点图
    plt.figure(figsize=(14, 10))
    scatter = plt.scatter(df['论文数'], df['平均引用次数'], 
                         s=df['引用次数']/100, alpha=0.7, 
                         c=df['排名'], cmap='viridis_r')
    
    plt.colorbar(scatter, label='全球排名 (颜色越深排名越好)')
    plt.xlabel('论文数量', fontsize=12)
    plt.ylabel('平均引用次数', fontsize=12)
    plt.title('华东师范大学各专业科研产出与影响力', fontsize=14, fontweight='bold')
    plt.grid(alpha=0.3)
    
    # 添加专业标签
    for i, major in enumerate(df['专业']):
        # 简化专业名称显示
        short_name = major.split('/')[0].split('&')[0].split(',')[0]
        if len(short_name) > 15:
            short_name = short_name[:15] + '...'
        plt.annotate(short_name, 
                    (df['论文数'].iloc[i], df['平均引用次数'].iloc[i]),
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    plt.tight_layout()
    scatter_path = os.path.join(output_dir, 'major_scatter.png')
    plt.savefig(scatter_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return {
        '专业数据热力图': 'major_heatmap.png',
        '专业排名分布': 'major_ranking.png',
        '科研产出影响力': 'major_scatter.png'
    }, df

def generate_major_data_report(charts, major_df):
    """生成专业数据的HTML报告"""
    
    # 计算统计指标
    total_majors = len(major_df)
    top_100 = len(major_df[major_df['排名'] <= 100])
    top_200 = len(major_df[major_df['排名'] <= 200])
    top_500 = len(major_df[major_df['排名'] <= 500])
    avg_rank = major_df['排名'].mean()
    best_rank = major_df['排名'].min()
    best_major = major_df.loc[major_df['排名'].idxmin(), '专业']
    highest_citation = major_df.loc[major_df['平均引用次数'].idxmax(), '专业']
    highest_avg_citation = major_df['平均引用次数'].max()
    
    # 获取当前时间（修复时间显示问题）
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>华东师范大学各专业ESI数据分析报告</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; line-height: 1.6; background-color: #f8f9fa; }}
            .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 15px; }}
            h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 15px; margin-top: 30px; }}
            .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
            .metric-box {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-top: 4px solid #3498db; }}
            .metric-value {{ font-size: 2.2em; font-weight: bold; color: #3498db; margin: 10px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
            th {{ background-color: #3498db; color: white; }}
            tr:nth-child(even) {{ background-color: #f8f9fa; }}
            .top-100 {{ background-color: #fff3cd; }}
            .top-200 {{ background-color: #e2e3e5; }}
            .top-500 {{ background-color: #d1ecf1; }}
            .chart {{ text-align: center; margin: 30px 0; padding: 20px; background: white; border-radius: 8px; }}
            .summary {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 25px; border-radius: 8px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; padding-top: 20px; border-top: 1px solid #ddd; }}
            .major-name {{ font-weight: bold; color: #2c3e50; }}
            .highlight {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .social-science {{ background-color: #e8f5e8 !important; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 华东师范大学各专业ESI数据分析报告</h1>
            
            <div class="summary">
                <h2>🎯 核心发现</h2>
                <p>基于华东师范大学{total_majors}个ESI学科的详细数据，分析各专业在全球的学术表现、科研产出和影响力。</p>
                <p>涵盖了排名、论文数量、引用次数等关键指标的综合分析。</p>
            </div>

            <div class="metrics">
                <div class="metric-box">
                    <div class="metric-value">{total_majors}</div>
                    <div>分析专业总数</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{best_rank}</div>
                    <div>最佳全球排名</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{avg_rank:.0f}</div>
                    <div>平均全球排名</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{top_100}</div>
                    <div>顶尖学科(前100)</div>
                </div>
            </div>
            
            <div class="highlight">
                <h3>🏆 亮点专业</h3>
                <p><strong>排名最佳专业</strong>: {best_major} (全球第{best_rank}名)</p>
                <p><strong>论文影响力最高</strong>: {highest_citation} (平均引用{highest_avg_citation}次)</p>
                <p><strong>科研产出最多</strong>: {major_df.loc[major_df['论文数'].idxmax(), '专业']} (共{major_df['论文数'].max()}篇论文)</p>
                <p><strong>社会科学表现</strong>: SOCIAL SCIENCES, GENERAL (全球第650名，在1888所机构中)</p>
            </div>
            
            <h2>📋 各专业详细数据表</h2>
            <table>
                <tr>
                    <th>专业名称</th>
                    <th>全球排名</th>
                    <th>总学校数</th>
                    <th>论文数量</th>
                    <th>引用次数</th>
                    <th>平均引用</th>
                    <th>全球前百分比</th>
                    <th>水平评估</th>
                </tr>
    """
    
    # 添加表格行
    for _, row in major_df.sort_values('排名').iterrows():
        rank = row['排名']
        total_schools = row['总学校数']
        papers = row['论文数']
        citations = row['引用次数']
        avg_citation = row['平均引用次数']
        percentile = round(rank / total_schools * 100, 2)
        
        # 设置水平和样式
        if rank <= 100:
            level = "⭐ 顶尖学科"
            row_class = "top-100"
        elif rank <= 200:
            level = "🔶 优秀学科"
            row_class = "top-200"
        elif rank <= 500:
            level = "📊 良好学科"
            row_class = "top-500"
        else:
            level = "🌍 一般学科"
            row_class = ""
        
        # 为社会科学添加特殊样式
        if 'SOCIAL SCIENCE' in row['专业']:
            row_class += " social-science"
        
        html_content += f"""
                <tr class="{row_class}">
                    <td class="major-name">{row['专业']}</td>
                    <td><strong>第{rank}名</strong></td>
                    <td>{total_schools}</td>
                    <td>{papers}</td>
                    <td>{citations}</td>
                    <td>{avg_citation}</td>
                    <td>前{percentile}%</td>
                    <td>{level}</td>
                </tr>
        """
    
    html_content += """
            </table>
            
            <h2>📈 专业数据可视化分析</h2>
    """
    
    # 添加图表
    for chart_name, chart_file in charts.items():
        html_content += f"""
            <div class="chart">
                <h3>{chart_name}</h3>
                <img src="{chart_file}" alt="{chart_name}" style="max-width: 95%; border-radius: 5px;">
            </div>
        """
    
    # 添加数据洞察
    html_content += f"""
            <div style="background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h2>💡 数据洞察</h2>
                <h3>优势领域:</h3>
                <ul>
                    <li><strong>化学(CHEMISTRY)</strong> - 全球第90名，在2141所机构中排名前4.2%</li>
                    <li><strong>数学(MATHEMATICS)</strong> - 全球第115名，在395所机构中排名前29.1%</li>
                    <li><strong>材料科学(MATERIALS SCIENCE)</strong> - 平均引用34.55次，论文影响力突出</li>
                    <li><strong>社会科学(SOCIAL SCIENCES)</strong> - 全球第650名，在1888所机构中排名前34.4%</li>
                </ul>
                
                <h3>改进机会:</h3>
                <ul>
                    <li>临床医学排名相对靠后(第2852名)，有较大提升空间</li>
                    <li>神经科学、药理学等生命科学领域论文数量相对较少</li>
                    <li>数学等基础学科平均引用次数较低，需提升论文影响力</li>
                </ul>
                
                <h3>学科分布:</h3>
                <ul>
                    <li>顶尖学科(前100): {top_100}个</li>
                    <li>优秀学科(101-200): {top_200 - top_100}个</li>
                    <li>良好学科(201-500): {top_500 - top_200}个</li>
                    <li>一般学科(500+): {total_majors - top_500}个</li>
                </ul>
            </div>
            
            <div class="footer">
                <p>⏰ 报告生成时间: {current_time}</p>
                <p>📚 数据来源: Clarivate ESI (Essential Science Indicators)</p>
                <p>💡 分析维度: 全球排名、论文产出、引用影响力等多维度评估</p>
                <p>💻 分析工具: Python数据分析与可视化</p>
                <p>📊 包含专业: {total_majors}个ESI学科，涵盖理工、医学、社会科学等领域</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    report_path = os.path.join(output_dir, "华东师范大学_各专业ESI数据分析报告.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"📄 专业数据HTML报告已生成: {report_path}")

def main_with_major_data():
    """主函数（包含专业数据）"""
    print("🚀 开始华东师范大学专业ESI数据分析...")
    
    # 创建专业数据可视化
    print("📊 创建专业数据可视化...")
    charts, major_df = create_major_data_table()
    
    # 生成专业数据报告
    print("📄 生成专业数据分析报告...")
    generate_major_data_report(charts, major_df)
    
    # 输出统计信息
    print(f"\n✅ 专业数据分析完成！")
    print(f"📊 分析了 {len(major_df)} 个专业的ESI数据")
    print(f"🥇 最佳排名专业: {major_df.loc[major_df['排名'].idxmin(), '专业']} (第{major_df['排名'].min()}名)")
    print(f"📈 最高影响力专业: {major_df.loc[major_df['平均引用次数'].idxmax(), '专业']} (平均引用{major_df['平均引用次数'].max()}次)")
    print(f"🌐 社会科学专业: SOCIAL SCIENCES, GENERAL (第650名)")
    print(f"📁 所有生成文件都保存在: {output_dir}")

if __name__ == "__main__":
    main_with_major_data()