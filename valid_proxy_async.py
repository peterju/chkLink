import asyncio
import json
import random
import re
from pprint import pprint

import aiohttp

SOURCE = "https://www.sslproxies.org/"
TARGET = "http://httpbin.org/get"

# 加入 User-Agent
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


async def fetch_proxies():
    async with aiohttp.ClientSession() as session:
        async with session.get(SOURCE, headers=headers) as response:
            text = await response.text()
            proxy_ips = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', text)  # 「\d+」代表數字一個位數以上
            return proxy_ips


async def check_proxy(session, ip):
    try:
        proxy = f"https://{ip}"
        await asyncio.sleep(1)  # 加上1秒的延遲
        async with session.get(TARGET, headers=headers, proxy=proxy, ssl=False, timeout=10) as response:
            if response.status == 200:
                print(f"使用 Proxy IP：{ip} 成功")
                return ip
            else:
                print(f"使用 Proxy IP：{ip} 失敗")
    except Exception as e:
        print(f"使用 {ip} 發生例外 , 錯誤訊息：{e}")
    return None


async def main():
    # 從 valid_proxy.json 讀取之前的有效 Proxy IP
    try:
        with open('valid_proxy.json', 'r') as f:
            valid_ips = set(json.load(f))
    except FileNotFoundError:
        valid_ips = set()

    # 取得新的 Proxy IP
    proxy_ips = await fetch_proxies()
    print(f"自 {SOURCE} 共取得 {len(proxy_ips)} 個 Proxy IP")

    # 將新的 Proxy IP 與之前的合併
    valid_ips.update(proxy_ips)

    async with aiohttp.ClientSession() as session:
        tasks = [check_proxy(session, ip) for ip in list(valid_ips)]
        results = await asyncio.gather(*tasks)  # 等待所有非同步任務完成
        valid_ips = set(ip for ip in results if ip)  # 從結果中取出有效的 Proxy IP 並轉換為集合，並更新 valid_ips

    # 輸出有效的 Proxy IP
    print("\n有效的 Proxy IP：")
    if valid_ips:
        pprint(valid_ips)
        print(f"共 {len(valid_ips)} 個")

    # 將有效的 Proxy IP 寫入檔案
    with open('valid_proxy.json', 'w') as f:
        json.dump(list(valid_ips), f)

    # 使用範例：隨機選擇一個 Proxy IP
    if valid_ips:
        proxy = f"https://{random.choice(list(valid_ips))}"
        print(f"\n隨機選擇的 Proxy IP：{proxy}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(TARGET, headers=headers, proxy=proxy, ssl=False) as response:
                    if response.status == 200:
                        print("成功")
        except Exception as e:
            print(f"使用 Proxy IP：{proxy} 失敗, 錯誤訊息：{e}")
    else:
        print("沒有有效的 Proxy IP 可供選擇")


# 執行非同步任務
asyncio.run(main())
