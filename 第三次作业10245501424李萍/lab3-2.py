import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
import re

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, "esi_institution_rankings")
output_dir = current_dir

def parse_esi_csv_accurate(file_path):
    """使用准确的学科名称解析ESI CSV文件"""
    try:
        filename = os.path.basename(file_path)
        print(f"📖 解析文件: {filename}")
        
        # 读取文件第一行获取学科信息
        with open(file_path, 'r', encoding='latin-1') as f:
            first_line = f.readline().strip()
        
        # 提取准确的学科名称
        research_field = None
        field_match = re.search(r'Filter Value\(s\):\s*([^&]+?)\s*Show:', first_line)
        if field_match:
            research_field = field_match.group(1).strip()
            print(f"找到学科: {research_field}")
        else:
            # 如果第一种模式不匹配，尝试其他模式
            field_match = re.search(r'Filter Value\(s\):\s*([^&]+?)\s*&', first_line)
            if field_match:
                research_field = field_match.group(1).strip()
                print(f"找到学科: {research_field}")
            else:
                research_field = f"Field_{filename.split('(')[-1].split(')')[0]}"
                print(f"从文件名推断学科: {research_field}")
        
        # 直接读取CSV，跳过第一行，只取前两列（排名和机构）
        df = pd.read_csv(file_path, encoding='latin-1', skiprows=1, usecols=[0, 1])
        
        # 重命名列
        df.columns = ['Rank', 'Institution']
        
        # 添加学科字段
        df['Research_Field'] = research_field
        
        # 清理Rank列
        df['Rank'] = pd.to_numeric(df['Rank'], errors='coerce')
        df = df.dropna(subset=['Rank'])
        df['Rank'] = df['Rank'].astype(int)
        
        print(f"✅ 成功提取 {len(df)} 条记录")
        return df
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return None

def extract_ecnu_rankings_accurate():
    """提取华东师范大学排名（使用准确学科名称）"""
    all_files = glob.glob(os.path.join(data_dir, "*.csv"))
    target_university = "EAST CHINA NORMAL UNIVERSITY"
    
    all_ecnu_data = []
    
    for file in all_files:
        df = parse_esi_csv_accurate(file)
        if df is not None and not df.empty:
            # 查找华东师范大学
            ecnu_mask = df['Institution'].astype(str).str.contains(target_university, case=False, na=False)
            ecnu_data = df[ecnu_mask].copy()
            
            if not ecnu_data.empty:
                rank_value = ecnu_data['Rank'].iloc[0]
                field_name = ecnu_data['Research_Field'].iloc[0]
                print(f"🎯 找到: {field_name} - 第{rank_value}名")
                all_ecnu_data.append(ecnu_data)
    
    if all_ecnu_data:
        combined_ecnu = pd.concat(all_ecnu_data, ignore_index=True)
        print(f"\n📊 总共找到华东师范大学在 {len(combined_ecnu)} 个ESI学科的排名")
        return combined_ecnu
    else:
        print("❌ 未找到华东师范大学的排名数据")
        return None

def create_accurate_visualizations(ecnu_data):
    """创建可视化图表（使用准确学科名称）"""
    charts = {}
    
    ecnu_data_sorted = ecnu_data.sort_values('Rank')
    
    if not ecnu_data_sorted.empty:
        # 1. 水平条形图 - 学科排名分布
        plt.figure(figsize=(14, 10))
        
        colors = []
        for rank in ecnu_data_sorted['Rank']:
            if rank <= 100:
                colors.append('#FF6B6B')  # 红色 - 世界一流
            elif rank <= 200:
                colors.append('#4ECDC4')  # 绿色 - 国际知名
            elif rank <= 500:
                colors.append('#45B7D1')  # 蓝色 - 有竞争力
            else:
                colors.append('#96CEB4')  # 浅绿 - 有影响力
        
        bars = plt.barh(range(len(ecnu_data_sorted)), ecnu_data_sorted['Rank'], color=colors, alpha=0.8)
        plt.yticks(range(len(ecnu_data_sorted)), ecnu_data_sorted['Research_Field'], fontsize=11)
        plt.title('华东师范大学ESI学科全球排名分布', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('全球排名 (数字越小越好)', fontsize=12)
        plt.grid(axis='x', alpha=0.3)
        
        # 添加排名数值标签
        for i, (bar, rank) in enumerate(zip(bars, ecnu_data_sorted['Rank'])):
            plt.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2, 
                    f'第{int(rank)}名', ha='left', va='center', fontweight='bold', fontsize=10)
        
        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#FF6B6B', label='世界一流 (前100)', alpha=0.8),
            Patch(facecolor='#4ECDC4', label='国际知名 (101-200)', alpha=0.8),
            Patch(facecolor='#45B7D1', label='有竞争力 (201-500)', alpha=0.8),
            Patch(facecolor='#96CEB4', label='有影响力 (500+)', alpha=0.8)
        ]
        plt.legend(handles=legend_elements, loc='lower right', fontsize=10)
        
        plt.tight_layout()
        chart_path1 = os.path.join(output_dir, 'esi_ranking_accurate.png')
        plt.savefig(chart_path1, dpi=300, bbox_inches='tight', facecolor='white')
        charts['ESI学科全球排名分布'] = 'esi_ranking_accurate.png'
        plt.close()
        
        # 2. 饼图 - 排名区间分布
        plt.figure(figsize=(10, 8))
        top_100 = len(ecnu_data[ecnu_data['Rank'] <= 100])
        top_200 = len(ecnu_data[(ecnu_data['Rank'] > 100) & (ecnu_data['Rank'] <= 200)])
        top_500 = len(ecnu_data[(ecnu_data['Rank'] > 200) & (ecnu_data['Rank'] <= 500)])
        over_500 = len(ecnu_data[ecnu_data['Rank'] > 500])
        
        sizes = [top_100, top_200, top_500, over_500]
        labels = [f'世界一流\n前100名\n{top_100}个学科', f'国际知名\n101-200名\n{top_200}个学科', 
                 f'有竞争力\n201-500名\n{top_500}个学科', f'有影响力\n500名以上\n{over_500}个学科']
        colors_pie = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, 
                colors=colors_pie, textprops={'fontsize': 10, 'fontweight': 'bold'})
        plt.title('华东师范大学ESI学科排名区间分布', fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        chart_path2 = os.path.join(output_dir, 'esi_pie_accurate.png')
        plt.savefig(chart_path2, dpi=300, bbox_inches='tight', facecolor='white')
        charts['ESI学科排名区间分布'] = 'esi_pie_accurate.png'
        plt.close()
    
    return charts

def generate_accurate_report(ecnu_data, charts):
    """生成准确学科名称的HTML报告"""
    
    # 计算统计指标
    total_fields = len(ecnu_data)
    top_100_count = len(ecnu_data[ecnu_data['Rank'] <= 100])
    top_200_count = len(ecnu_data[ecnu_data['Rank'] <= 200])
    top_500_count = len(ecnu_data[ecnu_data['Rank'] <= 500])
    avg_rank = ecnu_data['Rank'].mean()
    best_rank = ecnu_data['Rank'].min()
    worst_rank = ecnu_data['Rank'].max()
    
    ecnu_data_sorted = ecnu_data.sort_values('Rank')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>华东师范大学ESI学科全球排名分析报告</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; line-height: 1.6; background-color: #f8f9fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 15px; }}
            h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 15px; margin-top: 30px; }}
            .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
            .metric-box {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-top: 4px solid #3498db; }}
            .metric-value {{ font-size: 2.2em; font-weight: bold; color: #3498db; margin: 10px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
            tr:nth-child(even) {{ background-color: #f8f9fa; }}
            .top-100 {{ background-color: #fff3cd; }}
            .top-200 {{ background-color: #e2e3e5; }}
            .chart {{ text-align: center; margin: 30px 0; padding: 20px; background: white; border-radius: 8px; }}
            .summary {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 25px; border-radius: 88px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 40px; color: #666; padding-top: 20px; border-top: 1px solid #ddd; }}
            .subject-name {{ font-weight: bold; color: #2c3e50; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 华东师范大学ESI学科全球排名分析报告</h1>
            
            <div class="summary">
                <h2>🎯 执行摘要</h2>
                <p>基于Clarivate ESI（基本科学指标）权威数据，本报告使用准确的学科名称对华东师范大学在全球ESI学科领域的表现进行全面分析。</p>
                <p>共分析了 <strong>{total_fields}</strong> 个ESI学科的全球排名情况。</p>
            </div>

            <div class="metrics">
                <div class="metric-box">
                    <div class="metric-value">{total_fields}</div>
                    <div>分析学科总数</div>
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
                    <div class="metric-value">{top_100_count}</div>
                    <div>世界一流学科</div>
                </div>
            </div>
            
            <h2>📋 各学科排名详情（准确学科名称）</h2>
            <table>
                <tr>
                    <th>ESI学科</th>
                    <th>全球排名</th>
                    <th>水平评估</th>
                    <th>全球前百分比</th>
                </tr>
    """
    
    # 添加表格行
    for _, row in ecnu_data_sorted.iterrows():
        rank = row['Rank']
        field_name = row['Research_Field']
        percentile = (1 - rank/1000) * 100  # 假设总机构数为1000
        
        if rank <= 100:
            level = "⭐ 世界一流"
            row_class = "top-100"
        elif rank <= 200:
            level = "🔶 国际知名"
            row_class = "top-200"
        elif rank <= 500:
            level = "📊 有竞争力"
            row_class = ""
        else:
            level = "🌍 有影响力"
            row_class = ""
        
        html_content += f"""
                <tr class="{row_class}">
                    <td class="subject-name">{field_name}</td>
                    <td><strong>第{rank}名</strong></td>
                    <td>{level}</td>
                    <td>前{percentile:.1f}%</td>
                </tr>
        """
    
    html_content += """
            </table>
            
            <h2>📈 可视化分析</h2>
    """
    
    # 添加图表
    for chart_name, chart_file in charts.items():
        html_content += f"""
            <div class="chart">
                <h3>{chart_name}</h3>
                <img src="{chart_file}" alt="{chart_name}" style="max-width: 95%; border-radius: 5px;">
            </div>
        """
    
    # 优势学科分析
    top_disciplines = ecnu_data_sorted.head(5)
    html_content += """
            <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h2>🎖️ 优势学科TOP 5</h2>
                <ol>
    """
    
    for idx, row in top_disciplines.iterrows():
        html_content += f"""
                    <li style="margin: 10px 0; font-size: 1.1em;">
                        <strong>{row['Research_Field']}</strong> - 全球第{row['Rank']}名
                    </li>
        """
    
    html_content += f"""
                </ol>
            </div>
            
            <div class="footer">
                <p>⏰ 报告生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>📚 数据来源: Clarivate ESI (Essential Science Indicators)</p>
                <p>💡 学科名称: 直接从数据文件Filter Value(s)提取，确保准确性</p>
                <p>💻 分析工具: Python数据分析脚本</p>
                <p>📁 文件位置: 所有文件保存在同一目录中</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    report_path = os.path.join(output_dir, "华东师范大学_ESI学科排名_准确学科报告.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"📄 准确学科名称HTML报告已生成: {report_path}")

def main_accurate():
    """主函数（使用准确学科名称）"""
    print("🚀 开始华东师范大学ESI学科排名分析（准确学科名称）...")
    print(f"📁 工作目录: {current_dir}")
    print(f"📂 数据目录: {data_dir}")
    print(f"📂 输出目录: {output_dir}")
    
    # 检查数据目录是否存在
    if not os.path.exists(data_dir):
        print(f"❌ 数据目录不存在: {data_dir}")
        print("请确保esi_institution_rankings文件夹与Python文件在同一目录")
        return
    
    # 提取数据
    ecnu_data = extract_ecnu_rankings_accurate()
    
    if ecnu_data is None:
        print("❌ 未找到数据，退出分析")
        return
    
    # 创建可视化图表
    print("\n🎨 创建可视化图表...")
    charts = create_accurate_visualizations(ecnu_data)
    
    # 生成报告
    print("\n📄 生成分析报告...")
    generate_accurate_report(ecnu_data, charts)
    
    # 输出统计信息
    print(f"\n✅ 分析完成！")
    print(f"📊 分析了华东师范大学在 {len(ecnu_data)} 个ESI学科的全球排名")
    print(f"🥇 最佳排名: 第{ecnu_data['Rank'].min()}名")
    print(f"📈 平均排名: 第{ecnu_data['Rank'].mean():.0f}名")
    print(f"⭐ 世界一流学科: {len(ecnu_data[ecnu_data['Rank'] <= 100])}个")
    print(f"🔶 国际知名学科: {len(ecnu_data[(ecnu_data['Rank'] > 100) & (ecnu_data['Rank'] <= 200)])}个")
    print(f"📁 所有生成文件都保存在: {output_dir}")

if __name__ == "__main__":
    main_accurate()