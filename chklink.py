import os
import subprocess
import tempfile
import threading
import tkinter as tk
from datetime import datetime
from idlelib.tooltip import Hovertip
from tkinter import filedialog, messagebox, scrolledtext
from urllib.parse import urlparse
import urllib.request

import ttkbootstrap as ttk  # https://github.com/israel-dryer/ttkbootstrap
import urllib3
import chklink_core as core
import chklink_config as app_config

form = None


def stop_scanning():
    '''中斷掃描'''
    global stop_scan
    stop_scan = True


def run_on_ui_thread(callback, wait=False):
    '''確保 UI 相關操作由主執行緒執行'''
    if threading.current_thread() is threading.main_thread() or form is None:
        return callback()

    if not wait:
        form.after(0, callback)
        return None

    done = threading.Event()
    result = {}

    def wrapped():
        try:
            result['value'] = callback()
        finally:
            done.set()

    form.after(0, wrapped)
    done.wait()
    return result.get('value')


def append_log(message: str, tag: str) -> None:
    '''在主執行緒更新掃描記錄視窗'''

    def write():
        log_console.config(state=tk.NORMAL)
        log_console.insert(tk.END, message + "\n", tag)
        log_console.see(tk.END)
        log_console.config(state=tk.DISABLED)

    run_on_ui_thread(write)


def clear_log_console() -> None:
    '''清空掃描記錄視窗，並維持唯讀狀態'''

    def clear():
        log_console.config(state=tk.NORMAL)
        log_console.delete(1.0, tk.END)
        log_console.config(state=tk.DISABLED)

    run_on_ui_thread(clear)


def set_scan_controls(is_scanning: bool) -> None:
    '''在主執行緒更新掃描按鈕狀態'''

    def update():
        if is_scanning:
            analysis_btn.config(state=tk.DISABLED, cursor='X_cursor')
            stop_btn.config(state=tk.NORMAL, cursor='hand2')
        else:
            analysis_btn.config(state=tk.NORMAL, cursor='hand2')
            stop_btn.config(state=tk.DISABLED, cursor='X_cursor')

    run_on_ui_thread(update)


def update_progress(value: int, maximum: int) -> None:
    '''在主執行緒更新進度列'''
    run_on_ui_thread(lambda: upd_progress_show.config(value=value, maximum=maximum))


def show_info_message(title: str, message: str) -> None:
    '''顯示資訊訊息'''
    run_on_ui_thread(lambda: messagebox.showinfo(title, message), wait=True)


def show_warning_message(title: str, message: str) -> None:
    '''顯示警告訊息'''
    run_on_ui_thread(lambda: messagebox.showwarning(title, message), wait=True)


def ask_question_message(title: str, message: str) -> str:
    '''顯示詢問訊息並取得回覆'''
    return run_on_ui_thread(lambda: messagebox.askquestion(title, message), wait=True)


def run_update():
    '''更新程式'''
    def parse_version(version_text: str) -> tuple:
        parts = []
        for item in str(version_text).strip().split('.'):
            try:
                parts.append(int(item))
            except ValueError:
                parts.append(item)
        return tuple(parts)

    try:
        local_version_info = app_config.ensure_local_version(app_config.DEFAULT_LOCAL_VERSION_PATH)
        app_config.read_config(config_file)
        remote_version_url, setup_url = app_config.resolve_update_urls()
        remote_version_file = os.path.join(tempfile.gettempdir(), 'chklink_RemoteVersion.yaml')
        setup_file = os.path.join(tempfile.gettempdir(), 'chklink_setup.exe')

        show_info_message("資訊", "開始檢查是否有新版本，請稍候...")
        urllib.request.urlretrieve(remote_version_url, remote_version_file)
        remote_version_info = app_config.load_yaml(remote_version_file)

        local_version = str(local_version_info.get('version', app_config.DEFAULT_APP_VERSION))
        remote_version = str(remote_version_info.get('version', app_config.DEFAULT_APP_VERSION))

        if parse_version(remote_version) <= parse_version(local_version):
            show_info_message("資訊", f"目前已是最新版本：{local_version}")
            return

        answer = ask_question_message(
            "資訊",
            f"目前版本：{local_version}\n伺服器版本：{remote_version}\n\n是否下載並啟動新版安裝程式？",
        )
        if answer != 'yes':
            return

        app_config.ensure_update_cmd(app_config.DEFAULT_UPDATE_CMD_PATH)
        show_info_message("資訊", "開始下載新版安裝程式，請稍候...")
        urllib.request.urlretrieve(setup_url, setup_file)
        if not os.path.exists(setup_file):
            raise FileNotFoundError(f"找不到下載後的安裝程式：{setup_file}")

        subprocess.Popen(['cmd', '/c', app_config.DEFAULT_UPDATE_CMD_PATH, setup_file], cwd=app_config.APP_BASE_DIR)
        run_on_ui_thread(lambda: form.after(300, form.destroy))
    except urllib.error.HTTPError as exc:
        show_warning_message(
            "升級失敗",
            f"無法下載更新檔案：HTTP {exc.code}\n\nRemoteVersion URL:\n{remote_version_url}\n\nSetup URL:\n{setup_url}",
        )
    except Exception as exc:
        show_warning_message("升級失敗", f"無法完成升級流程：{exc}")


def resource_path(*parts: str) -> str:
    '''取得程式內資源的實際路徑'''
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, *parts)


def parse_headers_text(text: str) -> dict:
    '''解析多行標頭文字並做基本驗證'''
    headers = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if ':' not in line:
            raise ValueError(f"請求的標頭第 {line_number} 行格式錯誤，應為 名稱: 值")
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ValueError(f"請求的標頭第 {line_number} 行格式錯誤，名稱與值都不可空白。")
        headers[key] = value
    return app_config.normalize_headers(headers)


def parse_url_text(text: str, field_name: str, require_non_empty: bool = False) -> list[str]:
    '''解析網址文字，支援逗號與換行分隔'''
    raw_items = []
    for line in text.splitlines():
        raw_items.extend(part for part in line.split(','))
    return app_config.validate_url_list(raw_items, field_name, require_non_empty=require_non_empty)


def collect_runtime_settings(require_scan_urls: bool) -> dict:
    '''收集並驗證目前 GUI 畫面上的設定'''
    layer = app_config.parse_positive_int(layer_txt.get(), "檢查連結的層數")
    timeout = app_config.parse_positive_int(timeout_txt.get(), "連線逾時秒數")
    alt_must = app_config.parse_yes_no(alt_must_txt.get(), "圖片是否必須有 alt 屬性")
    check_http = app_config.parse_yes_no(check_http_txt.get(), "檢查不安全的 http 協定")

    report_dir = report_dir_txt.get().strip()
    if not report_dir:
        raise ValueError("報告路徑不可空白。")
    if not os.path.isdir(report_dir):
        raise ValueError(f"報告路徑不存在：{report_dir}")

    headers = parse_headers_text(headers_txt.get(1.0, tk.END))
    avoid_urls = parse_url_text(avoid_urls_txt.get(1.0, tk.END), "避免檢查的網址清單")
    scan_urls = parse_url_text(
        start_url_txt.get(1.0, tk.END) if require_scan_urls else scan_urls_txt.get(1.0, tk.END),
        "想要檢查的網址清單",
        require_non_empty=require_scan_urls,
    )

    return {
        'layer': layer,
        'timeout': timeout,
        'alt_must': alt_must,
        'check_http': check_http,
        'skip_visited': check_var.get() == 1,
        'report_dir': report_dir,
        'headers': headers,
        'avoid_urls': avoid_urls,
        'scan_urls': scan_urls,
    }


def analysis_func():
    global stop_scan
    stop_scan = False  # 重置中斷變數
    clear_log_console()
    append_log("=》正在檢查掃描設定...", "INFO")
    try:
        scan_request = collect_runtime_settings(require_scan_urls=True)
    except ValueError as exc:
        show_warning_message("設定錯誤", str(exc))
        return

    append_log("=》設定檢查完成，準備初始化掃描環境...", "INFO")
    set_scan_controls(True)
    threading.Thread(target=queued_link_check, args=(scan_request,), daemon=True).start()


def queued_link_check(scan_request: dict) -> list:
    '''使用雙向佇列結構儲存網站中的連結'''
    global logger, browser, stop_scan

    append_log("=》正在啟動瀏覽器檢查元件，首次啟動可能需要稍候 10 到 30 秒...", "INFO")
    try:
        browser = core.create_webdriver()
    except RuntimeError as exc:
        append_log(str(exc), "ERROR")
        show_warning_message(
            "資訊",
            "無法啟動 Chrome，請確認已安裝 Chrome，且 Selenium Manager 可正常運作。",
        )
        set_scan_controls(False)
        return []

    append_log("=》瀏覽器檢查元件已就緒，正在載入掃描快取與佇列...", "INFO")
    start_time = datetime.now()  # 取得開始時間
    scan_urls = scan_request['scan_urls']
    scan_completed = True
    try:
        for start_url in scan_urls:
            if stop_scan:
                break  # 中斷掃描
            url_domain = urlparse(start_url).netloc  # 取得網域
            current_time = datetime.now()  # 取得目前時間
            filename = f"{url_domain}_{current_time.strftime('%m%d_%H%M')}"  # 建立檔案名稱，格式為 domain_月日_時分
            logger = core.create_logger(scan_request['report_dir'], filename)  # 建立 logger
            msg = f"=》開始掃描 {url_domain}..."
            logger.info(msg)
            append_log(msg, "INFO")

            options = core.ScanOptions(
                headers=scan_request['headers'],
                avoid_urls=scan_request['avoid_urls'],
                timeout=scan_request['timeout'],
                alt_must=scan_request['alt_must'] == 'yes',
                check_http=scan_request['check_http'] == 'yes',
                skip_visited=scan_request['skip_visited'],
                url_normalization=advanced_scan_settings['url_normalization'],
                download_link_rules=advanced_scan_settings['download_link_rules'],
                soft_404_rules=advanced_scan_settings['soft_404_rules'],
                redirect_rules=advanced_scan_settings['redirect_rules'],
            )

            def emit(level: str, message: str) -> None:
                tag = {
                    'error': 'ERROR',
                    'warning': 'WARNING',
                    'info': 'INFO',
                }.get(level, 'INFO')
                append_log(message, tag)

            context = core.ScanContext(
                logger=logger,
                visited_link=visited_link,
                browser=browser,
                emit=emit,
                should_stop=lambda: stop_scan,
            )
            all_err_links = core.scan_site(start_url, scan_request['layer'], options, context)
            report_dir = scan_request['report_dir']
            if all_err_links:
                core.write_report(report_dir, filename, all_err_links, include_http_links=True)  # 產生報告
                err_count = sum([len(rec['error_links']) for rec in all_err_links])
                msg = f"=》掃描 {url_domain} 完成，共有 {err_count} 個錯誤連結。"
                logger.info(msg)
                append_log(msg, "SUCCESS")
                msg = f"=》報告已存放於 {report_dir}..."
                logger.info(msg)
                append_log(msg, "SUCCESS")
            else:
                msg = f"=》太棒了！{url_domain} 沒有錯誤連結。"
                logger.info(msg)
                append_log(msg, "SUCCESS")
    except Exception as exc:
        scan_completed = False
        if logger is not None:
            logger.exception("掃描期間發生未預期錯誤")
        append_log(f"掃描期間發生未預期錯誤：{exc}", "ERROR")
        show_warning_message("掃描失敗", f"掃描期間發生未預期錯誤：{exc}")
    finally:
        if browser is not None:
            browser.quit()  # 關閉瀏覽器
        core.save_visited_link(visted_link_file, visited_link)  # 儲存已檢查過的連結
        set_scan_controls(False)
        end_time = datetime.now()  # 取得結束時間
        hours, remainder = divmod((end_time - start_time).seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        msg = f"=》全部掃描完成！共花費 {hours} 小時 {minutes} 分 {seconds} 秒。"
        if logger is not None:
            logger.info(msg)
            core.close_logger(logger)
        append_log(msg, "SUCCESS")

    if not scan_completed:
        return []

    answer = ask_question_message("資訊", "掃描完成！是否要開啟檔案所在目錄？")
    if answer == 'yes':
        subprocess.Popen(f'explorer "{scan_request["report_dir"]}"')


def choose_dir():
    '''更改分析後產生的文件目錄'''
    folder_selected = filedialog.askdirectory(initialdir='shell:personal', title="請選擇下載目錄")
    if folder_selected:  # 若有選擇目錄
        dl_folder = folder_selected.replace("/", "\\")  # 將路徑中的 / 替換為 \\
        report_dir_txt.delete(0, tk.END)  # 清空下載目錄 report_dir_txt
        report_dir_txt.insert(0, dl_folder)  # 將選擇的目錄顯示在 report_dir_txt


def clear_start_url():
    '''清除 start_url 的內容'''
    start_url_txt.delete(1.0, tk.END)  # 清空 start_url
    clear_log_console()


def save_config() -> None:
    '''儲存設定檔'''
    global advanced_scan_settings
    try:
        config_values = collect_runtime_settings(require_scan_urls=False)
    except ValueError as exc:
        show_warning_message("設定錯誤", str(exc))
        return

    start_url_txt.delete(1.0, tk.END)  # 清空 start_url
    start_url_txt.insert(1.0, ",".join(config_values['scan_urls']) if config_values['scan_urls'] else "")  # 顯示想要檢查的網址

    current_config = app_config.load_yaml(config_file)

    # 更新設定值
    current_config['layer'] = config_values['layer']
    current_config['timeout'] = config_values['timeout']
    current_config['alt_must'] = config_values['alt_must']
    current_config['check_http'] = config_values['check_http']
    current_config['skip_visited'] = 'yes' if config_values['skip_visited'] else 'no'
    current_config['rpt_folder'] = config_values['report_dir']
    current_config['headers'] = config_values['headers']
    current_config['avoid_urls'] = config_values['avoid_urls']
    current_config['scan_urls'] = config_values['scan_urls']

    # 將更新後的設定寫回檔案，保留註解
    app_config.dump_yaml(config_file, current_config)
    advanced_scan_settings = app_config.resolve_scan_advanced_settings(current_config)

    msg = "設定檔已儲存。"
    append_log(msg, "INFO")
# 設定全域變數
stop_scan = False
app_config.migrate_legacy_runtime_files()
config_file = app_config.DEFAULT_CONFIG_PATH
setting = app_config.read_config(config_file)  # 讀取設定檔 data\config.yaml，若設定檔存在則讀取，否則建立設定檔

# 檢查並補充缺少的設定
setting, updated = app_config.normalize_setting(setting, os.path.join(os.environ['USERPROFILE'], 'Documents'))
advanced_scan_settings = app_config.resolve_scan_advanced_settings(setting)
local_version = (
    app_config.load_yaml(app_config.DEFAULT_LOCAL_VERSION_PATH)
    if os.path.exists(app_config.DEFAULT_LOCAL_VERSION_PATH)
    else {'version': app_config.DEFAULT_APP_VERSION}
)

# 如果有更新設定，則將更新後的設定存回設定檔
if updated:
    app_config.dump_yaml(config_file, setting)


# 其它全域變數與設定
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # 關閉 SSL 不安全的警告訊息
logger = None  # 定義 logger
visted_link_file = app_config.DEFAULT_VISITED_LINK_PATH  # 已檢查過的連結檔案
visited_link = core.load_visited_link(visted_link_file)  # 載入已檢查過的連結檔案，供儲存已檢查過的連結與回應狀態碼
browser = None  # 定義瀏覽器物件

# 建立主視窗
form = ttk.Window(themename="superhero")
form.title(f"{app_config.APP_DISPLAY_NAME} Ver.{local_version.get('version', app_config.DEFAULT_APP_VERSION)}")  # 設定視窗標題
form.geometry("1024x768")  # 設定視窗寬高
form.resizable(True, True)
# 指定行和列的權重
form.rowconfigure(0, weight=1)
form.columnconfigure(0, weight=1)

form.option_add("*Font", "新細明體 11")  # 設定所有元件的字型為新細明體，大小為 11

# default_font = font.nametofont("TkDefaultFont")  # 取得預設字型
# default_font.configure(family="Courier New", size=11)  # 設定預設字型為新細明體，大小為 11
# form.option_add("*Font", default_font)  # 設定所有元件的字型為預設字型

# 建立頁籤元件 Notebook
notebook = ttk.Notebook(form)
notebook.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")

# 建立分頁
page1 = ttk.Frame(notebook)
page2 = ttk.Frame(notebook)
notebook.add(page1, text="網址掃描")
notebook.add(page2, text="系統設定")
page1.columnconfigure(0, weight=1)
page1.rowconfigure(2, weight=1)
page2.columnconfigure(0, weight=1)
page2.rowconfigure(3, weight=1)
page2.rowconfigure(4, weight=1)
page2.rowconfigure(5, weight=1)

# --- page1 ---
# 建立 frame1_1
frame1_1 = ttk.Labelframe(page1, text="URLs", style='success.TLabelframe')
frame1_1.grid(row=0, column=0, padx=5, pady=1, sticky="nsew")
frame1_1.columnconfigure(0, weight=1)

# 建立網址輸入框
start_url_txt = ttk.ScrolledText(frame1_1, wrap=tk.WORD, height=4, font=('Courier New', 10))
start_url_txt.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
start_url_txt.insert(1.0, ",".join(setting.get('scan_urls')) if setting.get('scan_urls') else "")
Hovertip(start_url_txt, '輸入想要掃描的網址，若有多個網址請以逗號隔開')

# 建立右鍵選單
start_url_context_menu = tk.Menu(start_url_txt, tearoff=0)
start_url_context_menu.add_command(label="剪下", command=lambda: start_url_txt.event_generate("<<Cut>>"))
start_url_context_menu.add_command(label="複製", command=lambda: start_url_txt.event_generate("<<Copy>>"))
start_url_context_menu.add_command(label="貼上", command=lambda: start_url_txt.event_generate("<<Paste>>"))
start_url_context_menu.add_separator()
start_url_context_menu.add_command(
    label="刪除",
    command=lambda: start_url_txt.delete(tk.SEL_FIRST, tk.SEL_LAST) if start_url_txt.get(1.0, tk.END) else None,
)
start_url_context_menu.add_command(label="清除", command=clear_start_url)
# 綁定右鍵事件
start_url_txt.bind("<Button-3>", lambda e: start_url_context_menu.post(e.x_root, e.y_root))
# bug fix: 修正 ttkbootstrap 無法在 ScrolledText 元件按下 Ctrl+A 選取所有文字的問題
# "d:\pyTest\chklink\.venv\Lib\site-packages\ttkbootstrap\window.py", line 104, in on_select_all
# if widget.__class__.__name__ in ("Text",'ScrolledText'):

# 建立掃描按鈕
analysis_btn = ttk.Button(
    frame1_1,
    text="掃描",
    command=analysis_func,
    bootstyle="success",
    cursor='hand2',
)
Hovertip(analysis_btn, '按下按鈕開始掃描網址內的失效連結')
analysis_btn.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

# 建立中斷按鈕
stop_btn = ttk.Button(
    frame1_1, text="中斷", command=stop_scanning, bootstyle="danger", cursor='X_cursor', state=tk.DISABLED
)
Hovertip(stop_btn, '按下按鈕中斷掃描')
stop_btn.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

# 建立 frame1_2
frame1_2 = ttk.Frame(page1)
frame1_2.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
check_var = tk.IntVar()
check_var.set(1 if app_config.parse_yes_no(setting.get('skip_visited', 'yes'), "跳過已檢查過的網址") == 'yes' else 0)
check_button = ttk.Checkbutton(frame1_2, text="跳過已檢查過的網址", variable=check_var)
check_button.grid(row=0, column=0, padx=5, pady=5, sticky="e")
frame1_2.columnconfigure(0, weight=1)

# 建立 frame1_3
frame1_3 = ttk.Labelframe(page1, text="掃描歷史", style='success.TLabelframe')
frame1_3.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
frame1_3.columnconfigure(0, weight=1)
frame1_3.rowconfigure(0, weight=1)

log_console = scrolledtext.ScrolledText(frame1_3, wrap=tk.WORD, font=('Courier New', 10))
log_console.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
log_console.tag_config('ERROR', foreground='#e64530')  # 設定 ERROR 的文字顏色
log_console.tag_config('INFO', foreground='#c5c6c4')  # 設定 INFO 的文字顏色
log_console.tag_config('WARNING', foreground='#ffcc00')  # 設定 WARNING 的文字顏色
log_console.tag_config('SUCCESS', foreground='#8ae234')  # 設定 SUCCESS 的文字顏色
log_console.config(state=tk.DISABLED)

# --- page2 ---
# 建立 frame2_1
frame2_1 = ttk.Frame(page2)
frame2_1.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
# 建立儲存設定按鈕
cfg_save_btn = ttk.Button(page2, text="儲存設定", command=save_config, bootstyle="info", cursor='hand2')
cfg_save_btn.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
# 建立檢查更新按鈕
run_upd_btn = ttk.Button(page2, text="檢查更新", command=run_update, bootstyle="warning", cursor='hand2')
run_upd_btn.grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky="nsew")

# 建立檢查連結的層數Label
layer_txt_label = ttk.Label(frame2_1, text="檢查連結的層數")
layer_txt_label.grid(row=0, column=0, padx=5)

# 建立檢查連結的層數
layer_txt = ttk.Entry(frame2_1, width=3)
layer_txt.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
layer_txt.insert(0, setting.get('layer'))  # 設定預設連結的層數

# 建立圖片是否必須有 alt 屬性Label
alt_must_txt_label = ttk.Label(frame2_1, text="圖片是否必須有 alt 屬性")
alt_must_txt_label.grid(row=0, column=2, padx=5)

# 建立圖片是否必須有 alt 屬性
alt_must_txt = ttk.Combobox(frame2_1, values=["no", "yes"], width=6)
alt_must_txt.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
alt_must_txt.set(setting.get('alt_must'))

# 建立檢查不安全的 http 協定 Label
check_http_txt_label = ttk.Label(frame2_1, text="檢查不安全的 http 協定")
check_http_txt_label.grid(row=0, column=4, padx=5)

# 建立檢查不安全的 http 協定
check_http_txt = ttk.Combobox(frame2_1, values=["no", "yes"], width=6)
check_http_txt.grid(row=0, column=5, padx=5, pady=5, sticky="ew")
check_http_txt.set(setting.get('check_http'))

# 建立 frame2_2
frame2_2 = ttk.Frame(page2)
frame2_2.grid(row=1, column=0, padx=1, pady=1, sticky="nsew")
# frame2_2.columnconfigure(1, weight=1)
frame2_2.columnconfigure(4, weight=1)

# 建立連線逾時秒數Label
timeout_txt_label = ttk.Label(frame2_2, text="連線逾時秒數")
timeout_txt_label.grid(row=0, column=1, padx=5)

# 建立連線逾時秒數
timeout_txt = ttk.Entry(frame2_2, width=3)
timeout_txt.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
timeout_txt.insert(0, setting.get('timeout'))  # 設定預設連線逾時秒數

# 建立結果存放Label
report_dir_txt_label = ttk.Label(frame2_2, text="報告路徑")
report_dir_txt_label.grid(row=0, column=3, padx=5, pady=5)

# 建立結果存放輸入框
report_dir_txt = ttk.Entry(frame2_2, font=('Courier New', 10))
report_dir_txt.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
report_dir_txt.insert(0, setting.get('rpt_folder'))  # 設定預設結果存放目錄

# 建立更改目錄按鈕
folder_icon_path = resource_path('icon', 'folder.png')
choose_dir_icon = tk.PhotoImage(file=folder_icon_path) if os.path.exists(folder_icon_path) else None  # 設定更改目錄按鈕的圖示
choose_dir_button = ttk.Button(
    frame2_2,
    text="更改目錄",
    command=choose_dir,
    bootstyle="success-outline",
    cursor='hand2',
    image=choose_dir_icon,
    compound=tk.LEFT,  # 將圖示放在文字的左邊
)
choose_dir_button.grid(row=0, column=5, padx=10)

upd_progress_show = ttk.Progressbar(page2, orient='horizontal', mode='determinate')
upd_progress_show.grid(row=2, column=0, columnspan=3, padx=5, pady=2, sticky="nsew")

# 建立 frame2_3 用 LabelFrame
frame2_3 = ttk.Labelframe(page2, text="請求的標頭", style='info.TLabelframe')
frame2_3.grid(row=3, column=0, columnspan=3, padx=3, pady=5, sticky="nsew")
frame2_3.columnconfigure(0, weight=1)
frame2_3.rowconfigure(0, weight=1)

# 建立請求的標頭
headers_txt = scrolledtext.ScrolledText(frame2_3, wrap=tk.WORD, font=('Courier New', 10))
headers_txt.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
for header in setting.get('headers'):
    headers_txt.insert(tk.END, f"{header}: {setting.get('headers')[header]}\n")

# 建立 frame2_4 用 LabelFrame
frame2_4 = ttk.Labelframe(page2, text="想要避免檢查的網址清單", style='info.TLabelframe')
frame2_4.grid(row=4, column=0, columnspan=3, padx=3, pady=5, sticky="nsew")
frame2_4.columnconfigure(0, weight=1)
frame2_4.rowconfigure(0, weight=1)

# 建立想要避免檢查的網址清單
avoid_urls_txt = scrolledtext.ScrolledText(frame2_4, wrap=tk.WORD, font=('Courier New', 10))
avoid_urls_txt.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
for url in setting.get('avoid_urls'):
    avoid_urls_txt.insert(tk.END, f"{url}\n")

# 建立 frame2_5 用 LabelFrame
frame2_5 = ttk.Labelframe(page2, text="想要檢查的網址清單", style='info.TLabelframe')
frame2_5.grid(row=5, column=0, columnspan=3, padx=3, pady=5, sticky="nsew")
frame2_5.columnconfigure(0, weight=1)
frame2_5.rowconfigure(0, weight=1)

# 建立想要檢查的網址清單
scan_urls_txt = scrolledtext.ScrolledText(frame2_5, wrap=tk.WORD, font=('Courier New', 10))
scan_urls_txt.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
for url in setting.get('scan_urls'):
    scan_urls_txt.insert(tk.END, f"{url}\n")

# 開始主迴圈
form.mainloop()
