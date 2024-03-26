import hashlib
import os
import subprocess
import time

import wget


def calculate_md5(filename):
    """計算文件的 MD5 雜湊值"""
    hasher = hashlib.md5()  # 建立一個 MD5 雜湊值物件
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):  # 以 4096 bytes 為一個 chunk 進行迭代
            hasher.update(chunk)  # 更新 MD5 雜湊值
    return hasher.hexdigest()  # 回傳 MD5 雜湊值


def download_and_replace_exe(url):
    '''下載新版的執行檔，並進行替換'''
    try:
        if os.path.isfile('new.exe'):
            os.remove('new.exe')

        # 下載新版的執行檔
        wget.download(url)  # 使用 wget 下載檔案

        # 計算新版執行檔的 MD5 雜湊值
        new_md5 = calculate_md5('new.exe')

        # 計算舊版執行檔的 MD5 雜湊值
        old_md5 = calculate_md5('chklink.exe')

        # 比較兩個 MD5 雜湊值，如果不同則進行替換
        if new_md5 != old_md5:
            # 關閉舊版的 GUI 程式
            subprocess.call(["taskkill", "/f", "/im", "chklink.exe"])

            # 替換舊版執行檔
            os.replace('new.exe', 'chklink.exe')

            # 啟動新版的 GUI 程式
            subprocess.Popen(["chklink.exe"])

            return "更新成功！"
        else:
            os.remove('new.exe')
            return "您的程式版本已是最新的了"

    except Exception as e:
        return "更新失敗: " + str(e)


# 主程式
url = 'https://filedn.com/lUx2mFXVGAyFPYDUlzHuvcR/new.exe'
print("下載新版程式...")
result = download_and_replace_exe(url)
print("\n", result)
time.sleep(6)
