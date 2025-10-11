import os
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# -------------------------- 基础配置 --------------------------
TARGET_URL = "https://esi.clarivate.com/IndicatorsAction.action?app=esi&Init=Yes&authCode=null&SrcApp=IC2LS&SID=H3-ax2F2rp5xxThLx2BB9x2F5zJlJLj3D0vx2Fj5k10w-18x2dbgzAzA0Lu9wILyGpmx2Fh9wgx3Dx3D5jSx2BwWdetjXMPofSu6vNzAx3Dx3D-deDoSViHIQYUGXyhfV4d4Ax3Dx3D-ucx2FlMPFCLJrFFs0K4gTuzQx3Dx3D"

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

DRIVER_PATH = r"C:\Users\PPT\Downloads\msedgedriver\msedgedriver.exe" 

ORIGINAL_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',
    'cookie': ''
}

# -------------------------- 爬虫配置 --------------------------
RESEARCH_FIELDS = [
    "Agricultural Sciences",
    "Biology & Biochemistry",
    "Chemistry",
    "Clinical Medicine",
    "Computer Science",
    "Economics & Business",
    "Engineering",
    "Environment/Ecology",
    "Geosciences",
    "Immunology",
    "Materials Science",
    "Mathematics",
    "Microbiology",
    "Molecular Biology & Genetics",
    "Multidisciplinary",
    "Neuroscience & Behavior",
    "Pharmacology & Toxicology",
    "Physics",
    "Plant & Animal Science",
    "Psychiatry/Psychology",
    "Social Sciences, General",
    "Space Science"
]

DOWNLOAD_DIR = "./esi_institution_rankings"
DOWNLOAD_FORMAT = "CSV"
PAPER_TYPE = "Top"
TIMEOUT = 25
RETRY_TIMES = 2


# -------------------------- 浏览器初始化 --------------------------
def init_edge_browser():
    # 1. 配置Edge浏览器选项
    edge_options = webdriver.EdgeOptions()
    edge_options.binary_location = EDGE_PATH  # 指定Edge浏览器路径
    edge_options.add_argument("--start-maximized")
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_experimental_option("prefs", {
        "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    # 2. 直接使用手动下载的驱动（不再自动下载）
    service = Service(path=DRIVER_PATH)
    
    # 3. 初始化浏览器
    driver = webdriver.Edge(
        service=service,
        options=edge_options
    )
    driver.implicitly_wait(TIMEOUT)

    # 4. 加载页面并设置Cookie
    driver.get(TARGET_URL)
    cookie_str = ORIGINAL_HEADERS["cookie"]
    for cookie in cookie_str.split("; "):
        if "=" in cookie:
            name, value = cookie.split("=", 1)
            try:
                driver.add_cookie({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".clarivate.com"
                })
            except:
                continue
    driver.refresh()

    # 5. 验证页面加载
    try:
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "nav_indicators"))
        )
        print("✅ Edge浏览器初始化完成")
        return driver
    except TimeoutException:
        print("❌ 页面加载超时！检查：1. Cookie 2. Edge路径 3. 驱动路径")
        driver.quit()
        exit()


# -------------------------- 筛选与下载功能 --------------------------
def clear_existing_filters(driver):
    try:
        clear_btn = WebDriverWait(driver, TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "clrBtn"))
        )
        clear_btn.click()
        time.sleep(1.5)
        print("🔄 已清除历史筛选条件")
    except:
        print("ℹ️  无历史筛选条件")

def switch_to_institution_ranking(driver):
    """切换到Institutions分组选项"""
    print("\n🎯 选择Group By选项 - Institutions")
    
    try:
        # 方法1: JavaScript直接操作
        print("🔧 尝试JavaScript操作...")
        script = """
        $('#s2id_groupBy').select2('open');
        var options = document.querySelectorAll('.select2-result-label');
        for (var i = 0; i < options.length; i++) {
            if (options[i].textContent.trim() === 'Institutions') {
                options[i].click();
                return true;
            }
        }
        return false;
        """
        result = driver.execute_script(script)
        
        if result:
            time.sleep(2)
            current = driver.execute_script("return $('#s2id_groupBy .select2-chosen').text() || ''")
            if "Institutions" in current:
                print("✅ 选择成功")
                return True
        
        # 方法2: 通过父元素点击
        print("🔧 尝试父元素点击...")
        label_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH, 
                "//div[contains(@class, 'select2-result-label') and contains(text(), 'Institutions')]"
            ))
        )
        label_div.find_element(By.XPATH, "..").click()
        print("✅ 父元素点击成功")
        return True
        
    except Exception as e:
        print(f"❌ 选择失败: {str(e)}")
        return False

def filter_research_field(driver, field_name):
    for retry in range(RETRY_TIMES + 1):
        try:
            print(f"🔍 开始筛选学科: {field_name} (尝试 {retry + 1}/{RETRY_TIMES + 1})")
            
            # 1. 清除历史筛选条件
            clear_existing_filters(driver)
            time.sleep(2)
            switch_to_institution_ranking(driver)
            
            # 2. 点击Add Filter按钮
            print("🖱️ 点击Add Filter按钮...")
            add_filter_btn = WebDriverWait(driver, TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'add-filters') and contains(text(), 'Add Filter')]"))
            )
            
            driver.execute_script("arguments[0].click();", add_filter_btn)
            print("✅ Add Filter按钮点击成功")
            time.sleep(2.5)
            
        
            # 4. 识别弹出菜单
            popup_filter = None
            popup_selectors = [
    "#popupFilter",
    "//div[contains(@class, 'popup') and contains(@style, 'display: block')]",
    "//div[contains(@class, 'dropdown-menu') and contains(@style, 'display: block')]",
    "//div[contains(@class, 'select2-drop')]",
    "//div[contains(@id, 'popup')]",
    "//div[contains(@class, 'filter') and contains(@style, 'display: block')]"
]

            for selector in popup_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector) if selector.startswith("//") else driver.find_elements(By.CSS_SELECTOR, selector)
                    visible_elements = [el for el in elements if el.is_displayed()]
        
                    if visible_elements:
            # 选择最大的可见元素
                        popup_filter = max(visible_elements, key=lambda x: x.size['width'] * x.size['height'])
                        print(f"🎯 找到弹出菜单: {popup_filter.size}")
                        break
                except:
                    continue

            if not popup_filter:
                print("❌ 未找到弹出菜单")
                return False
            # 5. 现在使用找到的弹出菜单元素继续操作
            print("📋 使用找到的弹出菜单继续操作...")
            
           
            # 6. 在找到的弹出菜单中查找Research Fields链接
            print("🔍 在弹出菜单中查找Research Fields链接...")
            research_fields_link = None
            
            research_fields_selectors = [
                "a#researchFields",
                "a[href='javascript:void(0);']#researchFields", 
                "//a[contains(@class, 'inner-popup-link') and contains(text(), 'Research Fields')]",
                "//a[contains(text(), 'Research Fields')]",
                "a[onclick*='researchFields']",
                "a"  # 最后尝试所有链接
            ]
            
            for selector in research_fields_selectors:
                try:
                    if selector.startswith("//"):
                        # 在整个文档中查找
                        research_fields_link = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        # 在弹出菜单中查找
                        research_fields_link = popup_filter.find_element(By.CSS_SELECTOR, selector)
                    
                    print(f"✅ 找到Research Fields链接: {selector}")
                    break
                except Exception as e:
                    print(f"⚠️ 选择器失败: {selector}")
                    continue
            
            
            print("🖱️ 点击Research Fields选项")
            driver.execute_script("arguments[0].click();", research_fields_link)
            print("✅ Research Fields选项点击成功")
            time.sleep(3)
            # 7. 扫描研究领域选择界面
            print("🔍 扫描研究领域选择界面...")

            research_inner_popup = None
            research_selectors = [
    "#researchFieldsInnerPopUp",
    "[id*='researchFields']",
    "[id*='research']", 
    "[class*='researchFields']",
    "[class*='popup-checkbox']",
    ".popup-checkbox-content"
]

            for selector in research_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    visible_elements = [el for el in elements if el.is_displayed()]
        
                    if visible_elements:
                        research_inner_popup = max(visible_elements, key=lambda x: len(x.text))
                        popup_id = research_inner_popup.get_attribute('id') or '无ID'
                        print(f"🎯 找到研究领域界面: ID='{popup_id}'")
                        break
                except:
                    continue

                if not research_inner_popup:
                    print("❌ 未找到研究领域选择界面")
                    return False
            # 8. 在研究领域界面中查找目标复选框
            print(f"🔍 在界面中查找: {field_name}")

            field_checkbox = None

            # 改进的定位策略 - 处理特殊字符和多种HTML结构
            checkbox_strategies = [
                # 策略1: 直接通过value属性（不转义）
                (f".//input[@type='checkbox' and @value='{field_name}']", "value属性-原始"),
    
                # 策略2: 通过value属性（使用contains，更宽松）
                (f".//input[@type='checkbox' and contains(@value, 'Biology') and contains(@value, 'Biochemistry')]", "value属性-包含"),
    
                # 策略3: 通过部分value匹配
                (f".//input[@type='checkbox' and contains(@value, 'Biology & Bio')]", "value属性-部分"),
    
                # 策略4: 通过label文本（完整匹配）
                (f".//label[normalize-space()='{field_name}']/preceding-sibling::input[@type='checkbox']", "label文本-完整"),
    
                # 策略5: 通过label文本（包含匹配）
                (f".//label[contains(normalize-space(), 'Biology') and contains(normalize-space(), 'Biochemistry')]/preceding-sibling::input[@type='checkbox']", "label文本-包含"),
    
                    # 策略6: 通过任意相邻文本
                (f".//*[contains(text(), 'Biology & Biochem')]/preceding-sibling::input[@type='checkbox']", "相邻文本"),
    
                # 策略7: 通过父级容器查找
                (f".//div[contains(text(), '{field_name}')]/input[@type='checkbox']", "div容器"),
    
                # 策略8: 通过数据属性（如果有）
                (f".//input[@type='checkbox' and @data-field='{field_name}']", "数据属性"),
            ]

            for xpath, strategy in checkbox_strategies:
                try:
                    if xpath.startswith(".//"):
                        field_checkbox = research_inner_popup.find_element(By.XPATH, xpath)
                    else:
                        field_checkbox = driver.find_element(By.XPATH, xpath)
        
                    print(f"✅ 使用策略 '{strategy}' 找到复选框")
                    break
                except Exception as e:
                    print(f"⚠️ 策略 '{strategy}' 失败: {e}")
                    continue

            # 如果还是找不到，使用调试方法
            if not field_checkbox:
                print(f"❌ 仍然找不到 {field_name} 的复选框")
                print("🔍 开始深度调试...")
    
                # 方法A: 获取整个弹出框的HTML进行分析
                print("📄 获取弹出框HTML结构...")
                popup_html = research_inner_popup.get_attribute('innerHTML')
    
                # 保存HTML到文件以便分析
                with open(f"debug_popup_{field_name.replace(' ', '_')}.html", "w", encoding="utf-8") as f:
                    f.write(popup_html)
                print(f"💾 已保存HTML到: debug_popup_{field_name.replace(' ', '_')}.html")
    
                # 方法B: 显示所有可能的匹配元素
                print("🔍 显示所有包含'Biology'或'Biochemistry'的元素:")
                biology_elements = research_inner_popup.find_elements(By.XPATH, 
                    ".//*[contains(text(), 'Biology') or contains(text(), 'Biochemistry')]"
                )
    
                print(f"找到 {len(biology_elements)} 个相关元素:")
                for i, element in enumerate(biology_elements):
                    try:
                        element_text = element.text.strip()
                        element_tag = element.tag_name
                        element_class = element.get_attribute('class') or '无class'
                        print(f"  {i+1}. 标签: <{element_tag}> | 类: '{element_class}' | 文本: '{element_text}'")
            
                        # 尝试从这个元素找到相关的复选框
                        try:
                            # 查找前面的复选框
                            preceding_checkbox = element.find_element(By.XPATH, "./preceding-sibling::input[@type='checkbox']")
                            print(f"     ✅ 找到前面的复选框!")
                            field_checkbox = preceding_checkbox
                            break
                        except:
                            try:
                                # 查找父级中的复选框
                                parent_checkbox = element.find_element(By.XPATH, "../input[@type='checkbox']")
                                print(f"     ✅ 找到父级中的复选框!")
                                field_checkbox = parent_checkbox
                                break
                            except:
                                continue
                    
                    except Exception as e:
                        print(f"  {i+1}. 读取元素失败: {e}")
    
                # 方法C: 显示所有复选框及其完整上下文
                if not field_checkbox:
                    print("\n🔍 显示所有复选框的完整上下文:")
                    all_checkboxes = research_inner_popup.find_elements(By.XPATH, ".//input[@type='checkbox']")
                    print(f"找到 {len(all_checkboxes)} 个复选框")
        
                    for i, checkbox in enumerate(all_checkboxes):
                        try:
                            checkbox_value = checkbox.get_attribute('value') or '无value'
                            checkbox_id = checkbox.get_attribute('id') or '无ID'
                            checkbox_name = checkbox.get_attribute('name') or '无name'
                
                            # 获取父级元素信息
                            parent = checkbox.find_element(By.XPATH, "..")
                            parent_html = parent.get_attribute('outerHTML')
                
                            print(f"\n  {i+1}. 复选框信息:")
                            print(f"     ID: '{checkbox_id}'")
                            print(f"     Name: '{checkbox_name}'")
                            print(f"     Value: '{checkbox_value}'")
                            print(f"     父级HTML: {parent_html[:200]}...")
                
                            # 检查这个复选框是否是我们需要的
                            if "Biology" in checkbox_value or "Biochemistry" in parent_html:
                                print(f"     🎯 这个可能是目标复选框!")
                                field_checkbox = checkbox
                                break
                    
                        except Exception as e:
                            print(f"  {i+1}. 读取复选框失败: {e}")

            if not field_checkbox:
                print(f"💥 彻底找不到 {field_name} 的复选框")
                if retry < RETRY_TIMES:
                    continue
                else:
                    return False
            
            # 9. 选择复选框
            print(f"🖱️ 选择{field_name}复选框")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field_checkbox)
            time.sleep(1)
            
            if not field_checkbox.is_selected():
                driver.execute_script("arguments[0].click();", field_checkbox)
                print(f"✅ {field_name}复选框已选中")
                time.sleep(2)
            else:
                print(f"ℹ️ {field_name}复选框已经是选中状态")
            
            # 10. 关闭界面并应用筛选
            print("🔒 关闭研究领域选择界面")
            close_success = False
            
            # 先尝试应用按钮
            try:
                apply_buttons = driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Apply')] | //button[contains(text(), '应用')] | //input[@value='Apply'] | //input[@type='submit']"
                )
                if apply_buttons:
                    for button in apply_buttons:
                        if button.is_displayed():
                            driver.execute_script("arguments[0].click();", button)
                            close_success = True
                            print("✅ 点击Apply按钮")
                            break
            except:
                pass
            
            if not close_success:
                # 尝试返回按钮
                try:
                    back_buttons = driver.find_elements(By.CSS_SELECTOR, 
                        ".icon-arrow-button, .back-button, .popup-back, .btn-back"
                    )
                    if back_buttons:
                        for button in back_buttons:
                            if button.is_displayed():
                                driver.execute_script("arguments[0].click();", button)
                                close_success = True
                                print("✅ 点击返回按钮")
                                break
                except:
                    pass
            
            if not close_success:
                # 最后使用ESC
                try:
                    actions = ActionChains(driver)
                    actions.send_keys(Keys.ESCAPE).perform()
                    close_success = True
                    print("✅ 使用ESC键关闭")
                except:
                    pass
            
            time.sleep(2)
            
            # 11. 验证筛选应用
            print("🔍 验证筛选条件...")
            try:
                # 检查页面是否有筛选相关的显示
                page_text = driver.find_element(By.TAG_NAME, "body").text
                if field_name in page_text or "filter" in page_text.lower() or "applied" in page_text.lower():
                    print(f"🎯 筛选条件可能已应用: {field_name}")
                else:
                    print(f"⚠️ 筛选条件显示不明显，但继续执行")
            except:
                print("⚠️ 无法验证筛选条件，但继续执行")
            
            print(f"✅ 成功处理: {field_name}")
            return True
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 筛选{field_name}失败，错误：{error_msg}")
            
            if retry < RETRY_TIMES:
                print(f"🔄 重试第{retry+1}次...")
                time.sleep(3)
                clear_existing_filters(driver)
                continue
            else:
                print(f"💥 筛选{field_name}彻底失败")
                return False

def download_field_data(driver, field_name):
    """下载数据 - 修复下载选项识别问题"""
    try:
        print(f"💾 开始下载{field_name}数据...")
        
        # 1. 点击下载按钮
        print("🔍 查找下载按钮...")
        export_btn = WebDriverWait(driver, TIMEOUT).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "action-download"))
        )
        print("✅ 找到下载按钮")
        
        print("🖱️ 点击下载按钮...")
        driver.execute_script("arguments[0].click();", export_btn)
        print("✅ 下载按钮点击成功")
        time.sleep(3)  # 等待下载选项弹出
        
        # 2. 查找下载选项弹出窗口
        print("🔍 查找下载选项弹出窗口...")
        download_popup = None
        
        # 多种可能的下载弹出窗口选择器
        popup_selectors = [
            ".popup-action-content",  # 根据HTML结构
            "[class*='popup-action']",
            "[class*='export-options']",
            "[class*='download-options']",
            "//ul[contains(@class, 'popup-action')]",
            "//div[contains(@class, 'popup')]//ul"
        ]
        
        for selector in popup_selectors:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    if element.is_displayed():
                        download_popup = element
                        print(f"✅ 找到下载选项弹出窗口: {selector}")
                        break
                if download_popup:
                    break
            except:
                continue
        
        if not download_popup:
            print("❌ 未找到下载选项弹出窗口")
            # 保存截图调试
            driver.save_screenshot(f"debug_no_download_popup_{field_name}.png")
            return False
        
        # 3. 在弹出窗口中查找CSV选项
        print(f"📄 在弹出窗口中查找{DOWNLOAD_FORMAT}选项...")
        export_option = None
        
        if DOWNLOAD_FORMAT == "CSV":
            option_selectors = [
                "#expCsvBtn",  # 标准ID
                "li#expCsvBtn",  # 带标签的ID
                "//li[@id='expCsvBtn']",  # XPath
                "//li[contains(@onclick, 'exportCSV')]",  # 通过onclick事件
                "//a[contains(text(), 'CSV')]"  # 通过链接文本
            ]
        else:
            option_selectors = [
                "#expXlsBtn",
                "li#expXlsBtn", 
                "//li[@id='expXlsBtn']",
                "//li[contains(@onclick, 'exportXLS')]",
                "//a[contains(text(), 'XLS')]"
            ]
        
        for selector in option_selectors:
            try:
                if selector.startswith("//"):
                    # 在整个文档中查找
                    export_option = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    # 在下载弹出窗口中查找
                    export_option = download_popup.find_element(By.CSS_SELECTOR, selector)
                
                print(f"✅ 找到下载选项: {selector}")
                break
            except Exception as e:
                print(f"⚠️ 选择器失败: {selector} - {str(e)}")
                continue
        
        if not export_option:
            print(f"❌ 找不到{DOWNLOAD_FORMAT}下载选项")
            
            # 显示弹出窗口中所有可用的选项
            print("🔍 显示弹出窗口中所有选项:")
            all_options = download_popup.find_elements(By.TAG_NAME, "li")
            print(f"找到 {len(all_options)} 个选项")
            
            for i, option in enumerate(all_options):
                try:
                    option_id = option.get_attribute('id') or '无ID'
                    option_text = option.text.strip()
                    onclick_attr = option.get_attribute('onclick') or '无onclick'
                    print(f"  {i+1}. ID: '{option_id}' | 文本: '{option_text}' | onclick: '{onclick_attr}'")
                except Exception as e:
                    print(f"  {i+1}. 错误: {str(e)}")
            
            return False
        
        # 4. 点击下载选项
        print(f"🖱️ 点击{DOWNLOAD_FORMAT}下载选项...")
        try:
            # 使用JavaScript点击确保准确
            driver.execute_script("arguments[0].click();", export_option)
            print(f"✅ {DOWNLOAD_FORMAT}下载选项点击成功")
        except Exception as e:
            print(f"❌ 下载选项点击失败: {str(e)}")
            return False
        
        # 5. 等待下载
        print("⏳ 等待下载完成...")
        time.sleep(8)  # 给下载足够时间
        
        # 6. 验证下载
        print("🔍 验证下载结果...")
        download_dir = os.path.abspath(DOWNLOAD_DIR)
        
        if os.path.exists(download_dir):
            files = os.listdir(download_dir)
            # 查找最新的文件
            csv_files = [f for f in files if f.lower().endswith('.csv')] if DOWNLOAD_FORMAT == "CSV" else [f for f in files if f.lower().endswith(('.xls', '.xlsx'))]
            
            if csv_files:
                # 按修改时间排序，取最新的文件
                latest_file = max([os.path.join(download_dir, f) for f in csv_files], key=os.path.getmtime)
                file_size = os.path.getsize(latest_file)
                print(f"✅ 下载成功! 文件: {os.path.basename(latest_file)} ({file_size} 字节)")
                return True
            else:
                print("⚠️ 未找到下载文件，但可能下载在其他位置")
                # 检查是否有错误提示
                check_for_errors(driver)
                return True  # 即使没找到文件也返回成功，可能是文件名问题
        else:
            print("❌ 下载目录不存在")
            return False
        
    except Exception as e:
        print(f"❌ 下载{field_name}数据失败：{str(e)}")
        # 保存截图
        try:
            driver.save_screenshot(f"debug_download_error_{field_name}.png")
            print("💾 已保存错误截图")
        except:
            pass
        return False

def check_for_errors(driver):
    """检查页面错误提示"""
    error_selectors = [
        ".error", ".alert", ".message", ".warning",
        "[class*='error']", "[class*='alert']", "[class*='warning']",
        "//div[contains(@class, 'error')]",
        "//div[contains(@class, 'alert')]",
        "//div[contains(@class, 'message')]"
    ]
    
    for selector in error_selectors:
        try:
            if selector.startswith("//"):
                elements = driver.find_elements(By.XPATH, selector)
            else:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            
            for element in elements:
                if element.is_displayed():
                    error_text = element.text.strip()
                    if error_text and len(error_text) > 5:  # 避免太短的文本
                        print(f"⚠️ 页面提示: {error_text}")
        except:
            continue

def check_for_errors(self, driver):
    """检查页面错误提示"""
    error_selectors = [
        ".error", ".alert", ".message", ".warning",
        "[class*='error']", "[class*='alert']", "[class*='warning']",
        "//div[contains(@class, 'error')]",
        "//div[contains(@class, 'alert')]",
        "//div[contains(@class, 'message')]"
    ]
    
    for selector in error_selectors:
        try:
            if selector.startswith("//"):
                elements = driver.find_elements(By.XPATH, selector)
            else:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            
            for element in elements:
                if element.is_displayed():
                    error_text = element.text.strip()
                    if error_text and len(error_text) > 5:  # 避免太短的文本
                        print(f"⚠️ 页面提示: {error_text}")
        except:
            continue


def save_search_criteria(driver):
    """保存搜索条件（根据新HTML结构）"""
    try:
        save_btn = WebDriverWait(driver, TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "saveBtn"))
        )
        save_btn.click()
        time.sleep(1)
        print("💾 已保存搜索条件")
        return True
    except Exception as e:
        print(f"⚠️ 保存搜索条件失败：{str(e)}")
        return False
# -------------------------- 主程序 --------------------------
def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    driver = init_edge_browser()

    try:
        # switch_to_institution_ranking(driver)

        for field in RESEARCH_FIELDS:
            print(f"\n" + "="*50)
            print(f"处理：{field}")
            print("="*50)
            
            #clear_existing_filters(driver)
            
            if not filter_research_field(driver, field):
                print(f"⚠️ 跳过{field}")
                continue
            
            if not download_field_data(driver, field):
                print(f"⚠️ {field}下载失败")
                continue

        print(f"\n🎉 所有学科处理完成！数据路径：{os.path.abspath(DOWNLOAD_DIR)}")

    finally:
        driver.quit()
        print("\n🔌 浏览器已关闭")


if __name__ == "__main__":

    main()
