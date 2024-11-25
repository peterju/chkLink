import sys

import requests


def get_status_code_and_content_length(url):
    try:
        response = requests.get(url, timeout=10)  # 設定超時時間為 8 秒
        status_code = response.status_code
        content_length = len(response.content)
        return status_code, content_length
    except requests.exceptions.RequestException as e:
        return f"Error: {e}", 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("請提供網址作為參數")
        sys.exit(1)

    url = sys.argv[1]
    status_code, content_length = get_status_code_and_content_length(url)
    print(f"網址: {url}, 狀態碼: {status_code}, 內容大小: {content_length} bytes")

    if content_length == 0:
        print("警告: 內容大小為 0，可能表示網頁內容是空的或未正確加載")
