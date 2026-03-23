import os
import time
from datetime import datetime

from urllib.parse import urlparse

import urllib3
import chklink_core as core
import chklink_config as app_config

ADVANCED_SCAN_SETTINGS = {}


def queued_link_check(start_url, depth_limit=1) -> list:
    '''使用雙向佇列結構儲存網站中的連結'''
    global logger, HEADERS, AVOID_URLS, browser

    options = core.ScanOptions(
        headers=HEADERS,
        avoid_urls=AVOID_URLS,
        timeout=TIMEOUT,
        alt_must=ALT_MUST.lower() == 'yes',
        check_http=CHECK_HTTP.lower() == 'yes',
        skip_visited=SKIP_VISITED.lower() == 'yes',
        url_normalization=ADVANCED_SCAN_SETTINGS['url_normalization'],
        download_link_rules=ADVANCED_SCAN_SETTINGS['download_link_rules'],
        soft_404_rules=ADVANCED_SCAN_SETTINGS['soft_404_rules'],
        redirect_rules=ADVANCED_SCAN_SETTINGS['redirect_rules'],
        request_control=ADVANCED_SCAN_SETTINGS['request_control'],
    )
    context = core.ScanContext(
        logger=logger,
        visited_link=visited_link,
        browser=browser,
    )
    return core.scan_site(start_url, depth_limit, options, context)

app_config.migrate_legacy_runtime_files()
config_file = app_config.DEFAULT_CONFIG_FILE
setting = app_config.read_config(
    config_file,
    on_missing=lambda: print("首次執行，已為您建立預設設定檔。"),
)  # 讀取設定檔 data\config.yaml，若設定檔存在則讀取，否則建立設定檔

# 檢查並補充缺少的設定
setting, lack_config = app_config.normalize_setting(setting, os.path.join(os.environ['USERPROFILE'], 'Documents'))
ADVANCED_SCAN_SETTINGS = app_config.resolve_scan_advanced_settings(setting)

# 如果有新的設定，則將新設定存回設定檔
if lack_config:
    app_config.dump_yaml(config_file, setting)

# 設定全域變數
LAYER = app_config.parse_positive_int(setting.get('layer'), '檢查連結的層數')  # 定義連結檢查層數
TIMEOUT = app_config.parse_positive_int(setting.get('timeout'), '連線逾時秒數')  # 定義逾時秒數
ALT_MUST = app_config.parse_yes_no(setting.get('alt_must'), '圖片是否必須有 alt 屬性')
CHECK_HTTP = app_config.parse_yes_no(setting.get('check_http'), '檢查不安全的 http 協定')
SKIP_VISITED = app_config.parse_yes_no(setting.get('skip_visited', 'yes'), '跳過已檢查過的網址')
HEADERS = app_config.normalize_headers(setting.get('headers') or {})
AVOID_URLS = app_config.validate_url_list(setting.get('avoid_urls') or [], '避免檢查的網址清單')
SCAN_URLS = app_config.validate_url_list(setting.get('scan_urls') or [], '想要檢查的網址清單', require_non_empty=True)
DOC_FOLDER = setting.get('rpt_folder')  # 定義報告存放目錄
# 其它設定
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # 關閉 SSL 不安全的警告訊息
visted_link_file = app_config.DEFAULT_VISITED_LINK_FILE  # 已檢查過的連結檔案
visited_link = core.load_visited_link(visted_link_file)  # 載入已檢查過的連結檔案，供儲存已檢查過的連結與回應狀態碼
# 定義瀏覽器物件
try:
    browser = core.create_webdriver()
except RuntimeError as exc:
    raise RuntimeError(
        "無法啟動 Chrome，請確認已安裝 Chrome，且 Selenium Manager 可正常運作。"
    ) from exc

# ---------------- 主程式 ----------------
start_time = datetime.now()  # 取得開始時間
for start_url in SCAN_URLS:
    url_domain = urlparse(start_url).netloc  # 取得網域
    current_time = datetime.now()  # 取得目前時間
    filename = f"{url_domain}_{current_time.strftime('%m%d_%H%M')}"  # 建立檔案名稱，格式為 domain_月日_時分

    logger = core.create_logger(DOC_FOLDER, filename, with_console=True)  # 建立 logger
    logger.info(f"=》開始掃描 {url_domain}...")
    result = queued_link_check(start_url, LAYER)  # 根據網址進行指定層數的連結檢查
    if result:
        core.write_report(DOC_FOLDER, filename, result, include_http_links=True)  # 產生報告
        err_count = sum([len(rec['error_links']) for rec in result])
        logger.info(f"=》掃描 {url_domain} 完成，共有 {err_count} 個錯誤連結。")
        logger.info(f"=》報告存放於 {DOC_FOLDER}...")
    else:
        logger.info(f"=》太棒了！{url_domain} 沒有錯誤連結。")

# 掃描結束
browser.quit()  # 關閉瀏覽器
core.save_visited_link(visted_link_file, visited_link)  # 儲存已檢查過的連結

end_time = datetime.now()  # 取得結束時間
hours, remainder = divmod((end_time - start_time).seconds, 3600)
minutes, seconds = divmod(remainder, 60)
logger.info(f"=》全部掃描完成！共花費：{hours} 小時 {minutes} 分鐘 {seconds} 秒。")

core.close_logger(logger)

os.system(f'explorer {DOC_FOLDER}')  # 開啟檔案存放目錄

time.sleep(10)
