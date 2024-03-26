import csv
import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# from urllib.parse import urlparse


def check_Links(allLinks, pageUrl):
    '''將所有的連結分類為內部連結或外部連結，並將結果存入 .csv 檔案中'''
    currentTime = datetime.datetime.now()
    # 建立檔案名稱，格式為 Links-月日_時分秒.csv
    filename = f"Links-{str(currentTime.month).zfill(2)}{str(currentTime.day).zfill(2)}_{str(currentTime.hour).zfill(2)}{str(currentTime.minute).zfill(2)}{str(currentTime.second).zfill(2)}.csv"

    with open(filename, 'w', newline='', encoding='utf8') as csvfile:
        fieldnames = ['Url', 'Link', 'Kind', 'FQDN', 'Result']  # 欄位名稱

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        internalLinks = externalLinks = invalidLinks = 0

        # 逐一檢查所有的連結
        for anchor in allLinks:
            link = anchor.get("href")  # 取得連結中的 href 屬性
            # link_domain = urlparse(link).netloc  # 取得連結的網域
            if link:
                link = link.strip()  # 移除連結中的空白
                if (
                    link == 'https://www.ncut.edu.tw'
                    or link == 'https://www.ncut.edu.tw/'
                    or link == '/'
                    or link.startswith("#")
                    or link.startswith("javascript")
                ):  # 若連結為首頁、/、錨點或 JavaScript，則略過
                    continue
                fqdn = urljoin(pageUrl, link)
                try:
                    status = requests.get(fqdn, headers=HEADERS, stream=True).status_code
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
                if link.startswith(pageUrl) or link.startswith("/"):  # 若連結為內部連結，則寫入檔案
                    internalLinks += 1
                    writer.writerow({'Url': pageUrl, 'Link': link, 'Kind': 'Internal', 'FQDN': fqdn, 'Result': status})
                else:  # 否則為外部連結
                    externalLinks += 1
                    writer.writerow({'Url': pageUrl, 'Link': link, 'Kind': 'External', 'FQDN': fqdn, 'Result': status})
                invalidLinks += 1 if status != 200 else 0
        writer = csv.writer(csvfile)

        print(f"內部連結數：{internalLinks}，外部連結數：{externalLinks}，其中無效連結數：{invalidLinks}")
        print(f"詳細資料請看 {filename}")


def parseLinks(pageHtml, pageUrl):
    '''解析網頁內容，並取得所有的連結'''
    soup = BeautifulSoup(pageHtml, 'html.parser')
    allLinks = soup.find_all('a')  # 取得所有的 <a> 標籤
    if len(allLinks) == 0:
        print("此網頁沒有連結！")
    else:
        check_Links(allLinks, pageUrl)  # 呼叫 check_Links 函式


def request_maker(url):
    '''對網頁發出請求, 並取得網頁內容'''
    try:
        # 若未輸入網址，則使用預設網址
        if not url:
            url = "https://cc.ncut.edu.tw/"
        response = requests.get(url, headers=HEADERS, stream=True)
        # 如果回應碼為 200 OK，則執行以下程式碼
        if response.status_code == 200:
            # 取得網頁內容
            pageHtml = response.text
            pageUrl = response.url
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
    max_layer = 3  # 探查深度
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    url = input("請輸入網址(https://cc.ncut.edu.tw/)：")
    request_maker(url)  # 呼叫 request_maker 函式
