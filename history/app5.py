import csv
import datetime
import re
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

TIMEOUT = 6  # 定義連線逾時秒數
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6,zh-CN;q=0.5,la;q=0.4',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
}  # 定義連線標頭


def is_valid(url, link) -> bool:
    '''檢查連結是否有效'''
    fqdn = urljoin(url, link)
    try:
        print(" " * 120, end="\r")  # 清除目前列
        print(f"檢查連結: {link} ... ", flush=True, end="")  # 顯示目前檢查的連結，不快取強制輸出後不換行
        response = requests.head(fqdn, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)  # 發送 HEAD 請求
        status = response.status_code  # 取得狀態碼
        print(f"狀態: {status}", end="\r")  # 顯示狀態碼，游標至目前列首
        return status in (200, 302, 403)
    except requests.exceptions.Timeout as e:
        print(f"連線逾時：{link}  錯誤訊息：{e}")
    except requests.exceptions.TooManyRedirects as e:
        print(f"重新導向次數過多：{link}  錯誤訊息：{e}")
    except requests.exceptions.RequestException as e:
        print(f"無法取得此網頁內容：{link}  錯誤訊息：{e}")
    except requests.exceptions.ConnectionError as e:
        print(f"無法連線至此網頁：{link}  錯誤訊息：{e}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP 錯誤：{link}  錯誤訊息：{e}")
    except Exception as e:
        print(f"其它錯誤：{link}  錯誤訊息：{e}")

    return False


def get_links(url) -> tuple:
    '''取得網頁中的所有內部連結與外部連結'''
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(response.content, 'html.parser')
        all_links = []  # 取得所有的連結
        inter_links = []  # 內部連結
        outer_links = []  # 外部連結
        all_links = [link.get('href') for link in soup.find_all('a', href=True)]  # 取得所有的a連結
        all_img_links = [link.get('src') for link in soup.find_all('img', src=True)]  # 取得所有的圖片連結
        # # 找到所有具有 href 屬性的屬性值
        # href_tags = soup.find_all(href=True)
        # print("All href attributes:")
        # for tag in href_tags:
        #     print(tag['href'])

        # # 找到所有具有 src 屬性的屬性值
        # src_tags = soup.find_all(src=True)
        # print("\nAll src attributes:")
        # for tag in src_tags:
        #     print(tag['src'])
        # input("Press Enter to continue...")

        all_links.extend(all_img_links)  # 合併上述二個連結到所有連結
        all_links = list(set(all_links))  # 去除重複的連結
        for link in all_links:
            if link.startswith(url) or link.startswith("/"):  # 若連結為內部連結
                inter_links.append(link)
            elif link.startswith(('http://', 'https://')):  # 若連結為外部連結
                outer_links.append(link)
        return (inter_links, outer_links)  # 回傳內部連結與外部連結
    except requests.RequestException:
        return ([], [])  # 若發生錯誤，則回傳空串列


def queued_link_check(start_url, depth_limit=1) -> list:
    '''使用雙向佇列結構儲存網站中的連結'''
    visited = set()  # 存放已經檢查過的連結
    queue = deque([(start_url, 0)])  # 存放待檢查的連結，設定目前深度為 0
    all_err_links = []  # 存放所有錯誤連結

    while queue:
        url, current_depth = queue.popleft()  # 取得待檢查的連結
        match = re.search(r".*\.\w{2,4}$", url)  # 是否符合具有副檔名的.xxx或.xxxx (例如: .7z, .php, .aspx)
        if match and not url.endswith(('html', 'htm')):  # 若連結為檔案且非網頁檔
            continue  # 跳過
        if url not in visited and current_depth <= depth_limit:  # 若連結未檢查過且深度未達到指定深度
            err_links = []  # 存放此次 url 的錯誤連結
            print(f"\n第 {current_depth} 層連結： {url}")
            visited.add(url)  # 將連結加入已檢查的集合
            inter_links, outer_links = get_links(url)  # 取得內部連結與外部連結
            err_inter_links = [link1 for link1 in inter_links if not is_valid(url, link1)]  # 取得錯誤的內部連結
            err_outer_links = [link2 for link2 in outer_links if not is_valid(url, link2)]  # 取得錯誤的外部連結
            err_links.extend(err_inter_links) if err_inter_links else err_links  # 將錯誤的內部連結加入錯誤連結集合
            err_links.extend(err_outer_links) if err_outer_links else err_links  # 將錯誤的外部連結加入錯誤連結集合
            err_links = list(set(err_links))  # 去除重複的錯誤連結
            exist_inter_links = [x for x in inter_links if x not in err_inter_links]  # 取得正確的內部連結
            # exist_outer_links = [x for x in outer_links if x not in err_outer_links]
            if err_links:
                rec = {
                    'depth': current_depth,
                    'url': url,
                    'err_links': err_links,
                }
                all_err_links.append(rec)  # 將錯誤連結加入錯誤連結集合

            # 將正確的內部連結加入待檢查的連結
            for link in exist_inter_links:
                if (
                    link and link.startswith((start_url, '/')) and current_depth <= depth_limit
                ):  # 若連結為內部連結且深度未達到指定深度
                    absolute_link = urljoin(url, link)  # 取得絕對連結
                    queue.append((absolute_link, current_depth + 1))  # 將絕對連結加入待檢查的連結
    return all_err_links


# 主程式
if __name__ == "__main__":
    default_url = "https://cc.ncut.edu.tw/"
    start_url = input(f"請輸入網址({default_url})：")
    start_url = default_url if start_url == "" else start_url  # 若未輸入網址，則使用預設網址
    result = queued_link_check(start_url, 4)

    url_domain = urlparse(start_url).netloc  # 取得網域
    current_time = datetime.datetime.now()
    # 建立檔案名稱，格式為 domain_月日時分.csv
    filename = f"{url_domain}_{current_time.strftime('%m%d%H%M')}"
    csvname = f"{filename}.csv"
    with open(csvname, 'w', newline='', encoding='Big5') as csvfile:
        fieldnames = ['層數', 'URL', '錯誤連結']  # 欄位名稱
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for rec in result:
            for link in rec['err_links']:
                writer.writerow({'層數': rec['depth'], 'URL': rec['url'], '錯誤連結': link})  # 寫入錯誤連結

    # print(f"\n錯誤連結數：{len(result)}")
