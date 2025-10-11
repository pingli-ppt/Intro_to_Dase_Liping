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
    'cookie': '_vwo_uuid_v2=D789522C695DCD7D8FE1FD4602B319CA7|e6f04fe42646ae295e59595aaab594a8; _vwo_uuid=D789522C695DCD7D8FE1FD4602B319CA7; _vis_opt_s=1%7C; _fbp=fb.1.1759136773298.778729658773151674; _biz_uid=f60d8dc4e222421afee0a95940f0c052; ELOQUA=GUID=3F7989E921264AB5B28E088F6139C15B; _zitok=2c1e02e8403cd842d9ba1759136775; OptanonAlertBoxClosed=2025-09-29T09:06:15.709Z; _gcl_au=1.1.1770451591.1759136776; _vwo_consent=1%2C1%3A~; _vwo_ds=3%3At_0%2Ca_0%3A0%241759136771%3A41.83383465%3A%3A%3A%3A4; _clck=1cminuk%5E2%5Efzq%5E0%5E2098; _biz_flagsA=%7B%22Version%22%3A1%2C%22XDomain%22%3A%221%22%2C%22ViewThrough%22%3A%221%22%7D; OptanonConsent=isGpcEnabled=0&datestamp=Mon+Sep+29+2025+18%3A18%3A43+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202503.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=cb810a63-2f38-40a1-be00-7560baccd77d&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0004%3A1%2CC0002%3A1&intType=1&geolocation=HK%3B&AwaitingReconsent=false; _biz_nA=10; _biz_pendingA=%5B%5D; _rdt_uuid=1759136773668.4003e3f7-7b06-44f1-a457-bc2022d38e32; _uetvid=8cd849c09d1311f098c4c7c1781fe1bf|d58qiz|1759141124831|7|1|bat.bing.com/p/insights/c/e; _ga_K6K0YXL6HJ=GS2.1.s1759140177$o2$g1$t1759141134$j50$l0$h1773801530; _ga_V1YLG54MGT=GS2.1.s1759140177$o2$g1$t1759141134$j50$l0$h70085599; _ga=GA1.2.572071149.1759136776; _ga_9R70GJ8HZF=GS2.1.s1759140176$o2$g1$t1759141235$j12$l0$h1804760684; __cf_bm=QuotHikxUKqLLbpIarEhjP.zmRPrXVd0t..wUTDVmq0-1760142018-1.0.1.1-RTwmy.HLPXJnlbMWOGwCrTFoSgZxSx7zmG5CSKBFApWK02TKzGEbAJPmEpPBFF6ey8rZvdDEete7ccITaPhr9pae_oFj8uIvjIY55HvyEC4; PSSID="H3-giSw8NCsV1fVdVQQBvzmx2FF0W9IGLXJHg-18x2d0LpEAytP8uLXs0XqhOfBNgx3Dx3DYP9LROQEMn4xxjb59NZy8Pgx3Dx3D-z5IhIRye0WmHCFGEsjVz6wx3Dx3D-z1QxxaOZpxxGCwkgLYEq4RcAx3Dx3D"; IC2_SID="H3-giSw8NCsV1fVdVQQBvzmx2FF0W9IGLXJHg-18x2d0LpEAytP8uLXs0XqhOfBNgx3Dx3DYP9LROQEMn4xxjb59NZy8Pgx3Dx3D-z5IhIRye0WmHCFGEsjVz6wx3Dx3D-z1QxxaOZpxxGCwkgLYEq4RcAx3Dx3D"; CUSTOMER_NAME="EAST CHINA NORMAL UNIV"; E_GROUP_NAME="IC2 Platform"; SUBSCRIPTION_GROUP_ID="260055"; SUBSCRIPTION_GROUP_NAME="EAST CHINA NORMAL UNIV_20151126590_1"; CUSTOMER_GROUP_ID="99582"; IP_SET_ID_NAME="E China Normal U"; IP_SET_ID="3204746"; ROAMING_DISABLED="true"; ACCESS_METHOD="IP"; userAuthType="TrustedIPAuth"; userAuthIDType="222.66.117.73"; esi.isLocalStorageCleared=true; _sp_ses.2f26=*; _sp_id.2f26=27436d10-f6f3-4e78-a2c0-475a25f7d4cf.1759140366.10.1760142115.1760009367.c13eedc5-391d-49b3-9720-ba697149765c; _gid=GA1.2.1570155722.1760142115; _gat=1; esi.Show=; esi.Type=; esi.FilterValue=; esi.GroupBy=; esi.FilterBy=; esi.authorsList=; esi.frontList=; esi.fieldsList=; esi.instList=; esi.journalList=; esi.terriList=; esi.titleList=; _ga_D5KRF08D0Q=GS2.2.s1760142118$o10$g0$t1760142118$j60$l0$h0; JSESSIONID=F920E7818CFE9C41E1C7EF7E6310A4A7; __cf_bm=MlgUvcXYm6PCa4B8fl0fUY5G4gigIIl4WtMhMEC0XBk-1760142131-1.0.1.1-cDVcn_QoUPKfMdV3zz0jSG_hn2g97AoPxyEnEm2MrFPKJXxX03Wta_syvb98OxhhpSc508.amnWnwa5enDw3FqCHy_Egv_IFVM83IvDTI1Q'
}

response = requests.get(url, headers=header)


time.sleep(0.1)  # 此处填写等待时间
print(response.text)