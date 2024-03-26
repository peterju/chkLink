import os
import subprocess
import time


def download_and_replace_exe():
    '''新舊版執行檔替換作業'''
    try:
        subprocess.call(["taskkill", "/f", "/im", "chklink.exe"])

        # 替換舊版執行檔
        os.replace('chklink_upd.exe', 'chklink.exe')

        # 啟動新版的 GUI 程式
        subprocess.Popen(["chklink.exe"])

        return "更新成功！"

    except Exception as e:
        return "更新失敗: " + str(e)


# 主程式
print("進行新舊版執行檔替換作業...")
result = download_and_replace_exe()
print("\n", result)
time.sleep(6)
