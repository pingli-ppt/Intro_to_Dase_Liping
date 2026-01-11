import pandas as pd
import requests
import time
import random
import logging
from datetime import datetime
import json

# -------------------------- 新增：日志配置（便于排查问题） --------------------------
logging.basicConfig(
    filename='stock_crawl.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def get_stock_list():
    """获取沪深京A股股票代码列表"""
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    # -------------------------- 修改：完善请求头（增加Cookie和更多浏览器字段） --------------------------
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'http://quote.eastmoney.com/',
        'Cookie': 'qgqp_b_id=af2eabb93db086bbd17850d2788b7f34; st_nvi=VKzGu9rEuoRlisT1rvgV49329; websitepoptg_api_time=1758984365664; nid=05dbba35d2bafeadc98c725173bf7950; nid_create_time=1758984365866; gvi=D0z9M6YzKXNgCvewqWfWr0d83; gvi_create_time=1758984365866; st_si=43408060553622; st_asi=delete; fullscreengg=1; fullscreengg2=1; st_pvi=89404651157329; st_sp=2025-09-27%2022%3A46%3A05; st_inirUrl=https%3A%2F%2Fcn.bing.com%2F; st_sn=10; st_psi=2025092818160824-111000300841-9674538534',  # 替换为浏览器真实Cookie
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive'
    }
    
    all_stocks = []
    page_size = 20  # 每页数量
    page = 1
    
    while True:
        params = {
            'pn': str(page),
            'pz': str(page_size), 
            'po': '1',
            'np': '1',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',
            'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23',  # 沪深A股
            'fields': 'f12,f13,f14',
            '_': str(int(time.time() * 1000))
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            data_json = response.json()
            
            # -------------------------- 修改：增加接口状态码判断 --------------------------
            if data_json.get('rc') != 0:
                logging.warning(f"第{page}页接口返回错误：{data_json.get('msg')}（rc={data_json.get('rc')}）")
                break
                
            if data_json['data'] is None:
                logging.info("未获取到数据，可能已到最后一页")
                break
                
            total_count = data_json['data']['total'] if 'total' in data_json['data'] else 0
            df_data = data_json['data']['diff']
            
            current_page_stocks = []
            
            if isinstance(df_data, list):
                for stock_info in df_data:
                    market_code = f"{stock_info['f13']}.{stock_info['f12']}"
                    stock_name = stock_info['f14']
                    current_page_stocks.append((market_code, stock_name))
            elif isinstance(df_data, dict):
                for stock_info in df_data.values():
                    market_code = f"{stock_info['f13']}.{stock_info['f12']}"
                    stock_name = stock_info['f14']
                    current_page_stocks.append((market_code, stock_name))
            else:
                logging.warning(f"未知的数据类型: {type(df_data)}")
                break
            
            if not current_page_stocks:
                logging.info("当前页无数据，停止获取")
                break
                
            all_stocks.extend(current_page_stocks)
            logging.info(f"第{page}页获取到 {len(current_page_stocks)} 只股票，累计 {len(all_stocks)} 只")
            
            # 判断是否还有更多数据
            if len(current_page_stocks) < page_size:
                logging.info("已获取所有数据")
                break
                
            page += 1
            
            # -------------------------- 修改：增加随机延时（避免固定间隔） --------------------------
            time.sleep(random.uniform(1, 2))  # 1-2秒随机延时
            
        except Exception as e:
            logging.error(f"获取第{page}页股票列表失败: {e}")
            break
    
    if not all_stocks:
        logging.warning("未获取到股票列表，返回示例数据")
        return [
            ('1.000001', '平安银行'), 
            ('0.600000', '浦发银行'),
            ('0.000001', '上证指数'),
            ('1.000002', '万科A'),
            ('0.600036', '招商银行'),
            ('1.300750', '宁德时代')
        ]
    
    logging.info(f"成功获取 {len(all_stocks)} 只股票列表")
    
    # 去重并显示前10只作为示例
    unique_stocks = list(dict.fromkeys(all_stocks))  # 保持顺序去重
    print("前10只股票示例:")
    for i, (code, name) in enumerate(unique_stocks[:10]):
        print(f"{i+1}. {name} ({code})")
    
    return unique_stocks

def get_historical_kline(stock_code, retry=2):
    """获取股票的历史K线数据"""
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    
    # 判断是否为ETF（根据代码前缀）
    is_etf = any(etf_prefix in stock_code for etf_prefix in ['1.51', '1.58', '1.56', '0.159'])
    
    for attempt in range(retry + 1):
        try:
            params = {
                'secid': stock_code,
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': '101',  # 日K线
                'fqt': '1',    # 前复权
                'beg': '20140101',  # 开始日期
                'end': datetime.now().strftime('%Y%m%d'),  # 结束日期
                '_': str(int(time.time() * 1000))
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Referer': 'https://quote.eastmoney.com/',
                'Cookie': 'qgqp_b_id=af2eabb93db086bbd17850d2788b7f34; st_nvi=VKzGu9rEuoRlisT1rvgV49329; websitepoptg_api_time=1758984365664; nid=05dbba35d2bafeadc98c725173bf7950; nid_create_time=1758984365866; gvi=D0z9M6YzKXNgCvewqWfWr0d83; gvi_create_time=1758984365866; st_si=43408060553622; st_asi=delete; fullscreengg=1; fullscreengg2=1; st_pvi=89404651157329; st_sp=2025-09-27%2022%3A46%3A05; st_inirUrl=https%3A%2F%2Fcn.bing.com%2F; st_sn=10; st_psi=2025092818160824-111000300841-9674538534',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            data_json = response.json()
            
            if data_json.get('rc') != 0:
                if attempt < retry:
                    logging.warning(f"股票 {stock_code} 第{attempt+1}次重试（错误：{data_json.get('msg')}）")
                    time.sleep(3)
                    continue
                else:
                    logging.error(f"股票 {stock_code} 接口返回错误：{data_json.get('msg')}")
                    return pd.DataFrame()
                    
            if data_json.get('data') is None:
                logging.warning(f"股票 {stock_code} 无历史数据")
                return pd.DataFrame()
                
            klines = data_json['data']['klines']
            
            if not klines:
                logging.info(f"股票 {stock_code} 无K线数据")
                return pd.DataFrame()
                
            data = []
            for kline in klines:
                items = kline.split(',')
                if len(items) >= 6:
                    date_str = items[0]
                    try:
                        high_price = float(items[3])
                        low_price = float(items[4])
                        
                        # -------------------------- 新增：ETF数据乘以10 --------------------------
                        if is_etf:
                            high_price = high_price * 10
                            low_price = low_price * 10
                            logging.debug(f"ETF {stock_code} 价格已乘以10: 高{items[3]}→{high_price}, 低{items[4]}→{low_price}")
                        
                        data.append([date_str, high_price, low_price])
                    except ValueError as e:
                        logging.warning(f"K线数据解析失败（{date_str}）：{e}")
                        continue
            
            if not data:
                return pd.DataFrame()
                
            df = pd.DataFrame(data, columns=['date', 'high', 'low'])
            df['date'] = pd.to_datetime(df['date'])
            
            if is_etf:
                logging.info(f"ETF {stock_code} 获取到 {len(df)} 条历史数据（已×10）")
            else:
                logging.info(f"股票 {stock_code} 获取到 {len(df)} 条历史数据")
                
            return df
            
        except Exception as e:
            if attempt < retry:
                logging.warning(f"股票 {stock_code} 第{attempt+1}次重试（异常：{e}）")
                time.sleep(3)
            else:
                logging.error(f"获取 {stock_code} 历史K线失败: {e}")
                return pd.DataFrame()

# 3. 修复获取实时数据函数
def get_realtime_quote(stock_code, stock_name, retry=2):  # -------------------------- 修改：增加重试参数 --------------------------
    """获取股票的实时行情"""
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    
    # -------------------------- 修改：增加重试机制 --------------------------
    for attempt in range(retry + 1):
        try:
            params = {
                'secid': stock_code,
                'fields': 'f43,f58',  # -------------------------- 修改：只请求需要的字段（减少数据传输） --------------------------
                '_': str(int(time.time() * 1000))
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Referer': 'https://quote.eastmoney.com/',
                'Cookie': 'qgqp_b_id=af2eabb93db086bbd17850d2788b7f34; st_nvi=VKzGu9rEuoRlisT1rvgV49329; websitepoptg_api_time=1758984365664; nid=05dbba35d2bafeadc98c725173bf7950; nid_create_time=1758984365866; gvi=D0z9M6YzKXNgCvewqWfWr0d83; gvi_create_time=1758984365866; st_si=43408060553622; st_asi=delete; fullscreengg=1; fullscreengg2=1; st_pvi=89404651157329; st_sp=2025-09-27%2022%3A46%3A05; st_inirUrl=https%3A%2F%2Fcn.bing.com%2F; st_sn=10; st_psi=2025092818160824-111000300841-9674538534',  # 替换为浏览器真实Cookie
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data_json = response.json()
            
            # -------------------------- 修改：增加接口状态码判断 --------------------------
            if data_json.get('rc') != 0:
                if attempt < retry:
                    logging.warning(f"实时行情 {stock_code} 第{attempt+1}次重试（错误：{data_json.get('msg')}）")
                    time.sleep(3)
                    continue
                else:
                    logging.error(f"实时行情 {stock_code} 接口错误：{data_json.get('msg')}")
                    return None
                    
            if data_json.get('data') is None:
                logging.warning(f"股票 {stock_code} 无实时数据")
                return None
                
            data = data_json['data']
            current_price = data.get('f43')  # 最新价
            
            # -------------------------- 修改：修正价格单位处理（统一除以100） --------------------------
            if current_price is not None:
                # 接口返回单位为分，统一转换为元
                current_price = current_price / 100.0 if current_price != 0 else None
                # 若最新价为0，尝试用昨收价替代
                if current_price == 0:
                    current_price = data.get('f58') / 100.0 if data.get('f58') else None
            
            logging.info(f"股票 {stock_name} 实时价格: {current_price}")
            return current_price
            
        except Exception as e:
            if attempt < retry:
                logging.warning(f"实时行情 {stock_code} 第{attempt+1}次重试（异常：{e}）")
                time.sleep(3)
            else:
                logging.error(f"获取 {stock_code} 实时报价失败: {e}")
                return None

# 4. 获取ETF列表
def get_etf_list():
    """从东方财富网动态获取ETF基金列表"""
    url = "http://fund.eastmoney.com/data/rankhandler.aspx"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'http://fund.eastmoney.com/data/fbsfundranking.html',
        'Cookie': 'qgqp_b_id=af2eabb93db086bbd17850d2788b7f34; st_nvi=VKzGu9rEuoRlisT1rvgV49329; websitepoptg_api_time=1758984365664; nid=05dbba35d2bafeadc98c725173bf7950; nid_create_time=1758984365866; gvi=D0z9M6YzKXNgCvewqWfWr0d83; gvi_create_time=1758984365866; st_si=43408060553622; st_asi=delete; fullscreengg=1; fullscreengg2=1; st_pvi=89404651157329; st_sp=2025-09-27%2022%3A46%3A05; st_inirUrl=https%3A%2F%2Fcn.bing.com%2F; st_sn=10; st_psi=2025092818160824-111000300841-9674538534',  # 替换为浏览器真实Cookie
    }
    params = {
        'op': 'ph',
        'dt': 'fb',
        'ft': 'ct',  # 场内交易基金（ETF）
        'rs': '',
        'gs': '0',
        'sc': 'clrq',
        'st': 'desc',
        'pi': '1',
        'pn': '1293',  # -------------------------- 修改：减少单页请求量（避免触发反爬） --------------------------
        '_': str(int(time.time() * 1000))
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        data_text = response.text
        start_index = data_text.find('datas:[') + 6
        end_index = data_text.find(']', start_index)
        datas_str = data_text[start_index:end_index]
        
        etf_list = []
        if datas_str:
            items = datas_str.split('","')
            for item in items:
                fields = item.replace('"', '').split(',')
                if len(fields) >= 2:
                    fund_code = fields[0]
                    fund_name = fields[1]
                    # -------------------------- 修改：优化ETF市场代码判断逻辑 --------------------------
                    # 上交所ETF：510xxx、513xxx、515xxx等；深交所ETF：159xxx、15xxxx等
                    market_code = '1' if fund_code.startswith(('51', '58', '56')) else '0'
                    secid = f"{market_code}.{fund_code}"
                    etf_list.append((secid, fund_name))
        
        logging.info(f"成功获取 {len(etf_list)} 只ETF基金")
        for i, (code, name) in enumerate(etf_list[:5]):
            print(f"ETF示例 {i+1}: {name} ({code})")
        
        return etf_list
        
    except Exception as e:
        logging.error(f"动态获取ETF列表失败: {e}，返回示例数据")
        return [
            ('1.159919', '沪深300ETF'),
            ('1.510050', '上证50ETF'), 
            ('1.159915', '创业板ETF'),
            ('1.512480', '半导体ETF'),
            ('0.159607', '证券公司ETF')
        ]

def main():
    print("开始爬取股票和ETF数据...")
    all_results = []
    
    # 获取股票列表
    stock_list = get_stock_list()
    
    # 降低处理总量（原逻辑不变）
    max_process = 10000  
    processed_stocks = stock_list[:len(stock_list)]
    
    print(f"共获取到 {len(stock_list)} 只股票，本次处理前 {len(stock_list)} 只")
    
    # 获取ETF列表
    etf_list = get_etf_list()
    all_securities = processed_stocks + etf_list
    
    # 分批参数（原逻辑不变）
    batch_size = 20  
    batch_pause = random.randint(120, 180)  
    total = len(all_securities)
    batches = [(i, min(i + batch_size, total)) for i in range(0, total, batch_size)]
    
    print(f"将分 {len(batches)} 批处理，每批 {batch_size} 只，批间休息 {batch_pause} 秒")
    
    # 按批次处理
    for batch_idx, (start, end) in enumerate(batches, 1):
        batch_securities = all_securities[start:end]
        print(f"\n===== 开始处理第 {batch_idx}/{len(batches)} 批，共 {len(batch_securities)} 只 =====")
        
        for i, (security_code, security_name) in enumerate(batch_securities, 1):
            print(f"\n正在处理第 {start + i} 只证券(本批第 {i} 只): {security_name} ({security_code})")
            
            # 获取历史K线数据（原逻辑不变）
            hist_df = get_historical_kline(security_code)
            if hist_df.empty:
                print(f"跳过 {security_name}，无历史数据")
                continue
            
            # 计算历史价格（原逻辑不变）
            try:
                max_high_idx = hist_df['high'].idxmax()
                min_low_idx = hist_df['low'].idxmin()
                
                hist_high = hist_df.loc[max_high_idx, 'high']
                hist_high_date = hist_df.loc[max_high_idx, 'date']
                hist_low = hist_df.loc[min_low_idx, 'low']
                hist_low_date = hist_df.loc[min_low_idx, 'date']
            except Exception as e:
                logging.error(f"计算历史价格失败({security_code}): {e}")
                continue
            
            # 获取当前价格（原逻辑不变）
            current_price = get_realtime_quote(security_code, security_name)
            
            # -------------------------- 核心修改：处理股票代码，去掉小数点及前面的部分 --------------------------
            # 分割代码（如 "1.000001" → ["1", "000001"]，取索引1的元素）
            pure_code = security_code.split('.')[1]  # 关键代码：分割并提取纯证券代码
            
            # 存储结果：将原 "代码" 字段的值从 security_code 改为 pure_code
            result = {
                '代码': pure_code,  # 修改后：仅保留小数点后的纯代码（如 000001、510050）
                '名称': security_name,
                '历史最高价': round(hist_high, 3),
                '历史最高价日期': hist_high_date.strftime('%Y-%m-%d'),
                '历史最低价': round(hist_low, 3),
                '历史最低价日期': hist_low_date.strftime('%Y-%m-%d'),
                '当前价格': round(current_price, 3) if current_price is not None else 'N/A',
                '数据更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            all_results.append(result)
            
            print(f"完成处理: {security_name}")
            print(f"处理后代码: {pure_code} | 历史最高: {hist_high} (日期: {hist_high_date})")  # 新增：打印处理后代码
            print(f"历史最低: {hist_low} (日期: {hist_low_date})")
            print(f"当前价格: {current_price}")
            
            # 随机延时（原逻辑不变）
            time.sleep(random.uniform(3, 8))
        
        # 每批处理完成后休息（原逻辑不变）
        if batch_idx < len(batches):
            print(f"\n第 {batch_idx} 批处理完成，开始休息 {batch_pause} 秒...")
            time.sleep(batch_pause)
            batch_pause = random.randint(120, 180)
    
    # 保存到CSV（原逻辑不变，但"代码"字段已变为纯代码）
    if all_results:
        result_df = pd.DataFrame(all_results)
        filename = f'stock_etf_historical_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        result_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到 {filename}，共处理 {len(all_results)} 只证券")
        print("\n处理结果预览:")
        print(result_df.head().to_string(index=False))  # 预览中"代码"字段已无小数点
    else:
        print("未获取到有效数据")

if __name__ == "__main__":
    main()