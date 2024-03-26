import csv
import datetime
import json
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

TIMEOUT = 5  # 連線逾時秒數
MAX_LAYER = 2  # 探查深度
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

url_checked = {}  # 用來記錄已經檢查過的網址


def check_Links(allLinks, page_url, now_layer=0) -> None:
    '''將所有的連結逐一檢查，並將連結失效者寫入檔案'''
    # 逐一檢查所有的連結
    for anchor in allLinks:
        link = anchor.get("href")  # 取得連結中的 href 屬性

        if link:
            link = link.strip()  # 移除連結中的空白
            if (
                link == '/' or link.startswith("#") or link.startswith("javascript")
            ):  # 若連結為首頁、/、錨點或 JavaScript，則略過
                continue
            fqdn = urljoin(page_url, link)  # 取得完整的網址
            if fqdn not in url_checked:  # 若網址未檢查過
                url_checked[fqdn] = 1  # 紀錄檢查次數
                try:
                    response = requests.get(fqdn, headers=HEADERS, stream=True, timeout=TIMEOUT)
                    status = response.status_code
                except requests.exceptions.Timeout as e:
                    status = f"連線逾時\n錯誤訊息：{e}!"
                except requests.exceptions.TooManyRedirects as e:
                    status = f"重新導向次數過多\n錯誤訊息：{e}!"
                except requests.exceptions.RequestException as e:
                    status = f"無法取得此網頁內容\n錯誤訊息：{e}!"
                except requests.exceptions.ConnectionError as e:
                    status = f"無法連線至此網頁\n錯誤訊息：{e}!"
                except requests.exceptions.HTTPError as e:
                    status = f"HTTP 錯誤\n錯誤訊息：{e}!"
                except Exception as e:
                    status = f"發生錯誤\n錯誤訊息：{e}!"
                print(f"偵測：{link}，狀態：{status}")
                if status != 200:
                    write_to_csv(page_url, link, fqdn, status)
                else:
                    write_to_csv(page_url, link, fqdn, status)
                    if link.startswith(page_url) or link.startswith("/"):  # 若連結為內部連結
                        fqdn_html = response.text
                        fqdn_url = response.url
                        parseLinks(fqdn_html, fqdn_url, now_layer)  # 呼叫 parseLinks 函式
            else:  # 若網址已檢查過
                url_checked[fqdn] += 1  # 檢查次數+1


def parseLinks(pageHtml, pageUrl, this_layer=0) -> None:
    '''解析網頁內容，並取得所有的連結'''
    this_layer += 1
    if this_layer > MAX_LAYER:
        return
    else:
        soup = BeautifulSoup(pageHtml, 'html.parser')
        allLinks = soup.find_all('a')  # 取得所有的 <a> 標籤
        # for anchor in allLinks:
        #     link = anchor.get("href")  # 取得連結中的 href 屬性
        #     print(link)
        check_Links(allLinks, pageUrl, this_layer)  # 呼叫 check_Links 函式


def write_to_csv(page_url, link, fqdn, status) -> None:
    '''將失效連結寫入 CSV 檔案'''
    with open(csvname, 'a', newline='', encoding='Big5') as csvfile:
        fieldnames = ['Url', 'Link', 'Kind', 'FQDN', 'Result']  # 欄位名稱
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if link.startswith(page_url) or link.startswith("/"):  # 若連結為內部連結，則寫入檔案
            writer.writerow({'Url': page_url, 'Link': link, 'Kind': 'Internal', 'FQDN': fqdn, 'Result': status})
        else:  # 否則為外部連結
            writer.writerow({'Url': page_url, 'Link': link, 'Kind': 'External', 'FQDN': fqdn, 'Result': status})
        writer = csv.writer(csvfile)


def request_maker(url) -> None:
    '''對網頁發出請求, 並取得網頁內容'''
    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=TIMEOUT)
        # 如果回應碼為 200 OK，則執行以下程式碼
        if response.status_code == 200:
            pageHtml = response.text  # 取得網頁內容
            pageUrl = response.url  # 取得網頁網址
            parseLinks(pageHtml, pageUrl)  # 呼叫 parseLinks 函式
        else:
            print(f"連結無效，回應碼為 {response.status_code}!")
    except requests.exceptions.Timeout as e:
        print(f"連線逾時\n錯誤訊息：{e}!")
    except requests.exceptions.TooManyRedirects as e:
        print(f"重新導向次數過多\n錯誤訊息：{e}!")
    except requests.exceptions.RequestException as e:
        print(f"無法取得此網頁內容\n錯誤訊息：{e}!")
    except requests.exceptions.ConnectionError as e:
        print(f"無法連線至此網頁\n錯誤訊息：{e}!")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP 錯誤\n錯誤訊息：{e}!")
    except Exception as e:
        print(f"發生錯誤\n錯誤訊息：{e}!")


if __name__ == "__main__":
    default_url = "https://cc.ncut.edu.tw/"
    # default_url = "https://lgc.ncut.edu.tw/"
    url = input(f"請輸入網址({default_url})：")
    url = default_url if url == "" else url  # 若未輸入網址，則使用預設網址

    url_domain = urlparse(url).netloc  # 取得網域
    current_time = datetime.datetime.now()
    # 建立檔案名稱，格式為 domain_月日時分.csv
    filename = f"{url_domain}_{current_time.strftime('%m%d%H%M')}"
    csvname = f"{filename}.csv"
    with open(csvname, 'w', newline='', encoding='Big5') as csvfile:
        fieldnames = ['Url', 'Link', 'Kind', 'FQDN', 'Result']  # 欄位名稱
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    request_maker(url)  # 呼叫 request_maker 函式

    # 將 url_checked 寫入 json 檔案
    with open(filename + '.json', "w", encoding='Big5') as outfile:
        json.dump(url_checked, outfile, indent=2)
