import sys

import requests


def get_status_code(url):
    try:
        response = requests.get(url, timeout=10)  # 設定超時時間為 10 秒
        return response.status_code
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("請提供網址作為參數")
        sys.exit(1)

    url = sys.argv[1]
    status_code = get_status_code(url)
    print(f"網址: {url}, 狀態碼: {status_code}")
