# 透過 Proxy IP 來源網站取得 Proxy IP，並測試 Proxy IP 是否有效
import json
import random
import re
from pprint import pprint

import requests

SOURCE = "https://www.sslproxies.org/"  # Proxy IP 來源網站 （https）
TARGET = "http://httpbin.org/get"  # 測試網站 （http）

# 設定 HTTP 標頭
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6,zh-CN;q=0.5,la;q=0.4',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Cookie': '_ga_SNR7NPLEYG=GS1.1.1651249603.1.0.1651250646.0; _ga_BGEHGPV3SB=GS1.1.1707539001.1.1.1707539323.0.0.0; _gid=GA1.3.1607128698.1707801742; _ga=GA1.1.381372473.1651249604; _ga_Q0EL30K2K5=GS1.1.1707801741.1.0.1707801770.0.0.0; _ga_54MVLT2EZN=GS1.1.1707843944.5.1.1707843969.0.0.0; __RequestVerificationToken_L05ldFNlcnZpY2Vz0=MrnqY4BqFXwyAR3uGWq5prQZPEwGWyzIJgIpuGFLyP8hqJ6eLKM9EWlC8NVA4MZqmyjtxmWT-9ZtzrO04NCTXcM_njimY7J0_WFWHlyWtzE1',
    'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="131", "Chromium";v="131"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}

# 從 valid_proxy.json 讀取之前的有效 Proxy IP
try:
    with open('valid_proxy.json', 'r') as f:
        valid_ips = set(json.load(f))
except FileNotFoundError:
    valid_ips = set()

# 取得新的 Proxy IP
response = requests.get(SOURCE, headers=headers)  # 取得網頁內容
# 使用正規表達式取得 Proxy IP：「\d+」代表數字一個位數以上
proxy_ips = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', response.text)
print(f"自 {SOURCE} 共取得 {len(proxy_ips)} 個 Proxy IP")

# valid_ips 加入新取得的 Proxy IP
valid_ips.update(proxy_ips)

# 測試 valid_ips 中的 Proxy IP 是否有效
for ip in list(valid_ips):  # 將集合轉換為列表進行迭代
    try:
        response = requests.get(
            TARGET,
            headers=headers,
            # proxies={'http': ip, 'https': ip},
            proxies={'https': ip},
            timeout=5,
        )
        if response.status_code == 200:
            print(f"使用 Proxy IP：{ip} 成功")
        else:
            # 移除失效的 Proxy IP
            valid_ips.remove(ip)
            print(f"使用 Proxy IP：{ip} 失敗")
    except Exception as e:
        valid_ips.remove(ip)
        print(f"使用 Proxy IP：{ip} 失敗, 錯誤訊息：{e}")

# 輸出有效的 Proxy IP
print("\n有效的 Proxy IP：")
if valid_ips:
    pprint(valid_ips)
    print(f"共 {len(valid_ips)} 個")

# 將有效的 Proxy IP 寫入檔案
with open('valid_proxy.json', 'w') as f:
    json.dump(list(valid_ips), f)

# 使用範例：從 valid_proxy.json 讀取有效的 Proxy IP 並隨機選擇一個 Proxy IP 進行測試
if valid_ips:
    proxy = random.choice(list(valid_ips))
    print(f"\n隨機選擇的 Proxy IP：{proxy}")
    try:
        response = requests.get(
            TARGET, headers=headers, proxies={"https": proxy}, timeout=5
        )
        if response.status_code == 200:
            pprint(response.json())  # 輸出網頁內容
    except Exception as e:
        print(f"使用 Proxy IP：{proxy} 失敗, 錯誤訊息：{e}")
else:
    print("沒有有效的 Proxy IP 可供選擇")
