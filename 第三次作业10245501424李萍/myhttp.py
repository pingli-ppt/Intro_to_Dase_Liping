import os
import time
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

# 创建Excel文件
wb = Workbook()
ws = wb.active


# 爬取地址
url = f'https://esi.clarivate.com/IndicatorsAction.action?app=esi&Init=Yes&authCode=null&SrcApp=IC2LS&SID=H3-ax2F2rp5xxThLx2BB9x2F5zJlJLj3D0vx2Fj5k10w-18x2dbgzAzA0Lu9wILyGpmx2Fh9wgx3Dx3D5jSx2BwWdetjXMPofSu6vNzAx3Dx3D-deDoSViHIQYUGXyhfV4d4Ax3Dx3D-ucx2FlMPFCLJrFFs0K4gTuzQx3Dx3D'  # 此处填写目标网页URL

# 请求header
header = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',  # 此处填写浏览器标识
    'cookie': ''
}

response = requests.get(url, headers=header)


time.sleep(0.1)  # 此处填写等待时间

print(response.text)
