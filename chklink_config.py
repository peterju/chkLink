import os
from urllib.parse import urlparse

from ruamel.yaml import YAML

DEFAULT_TEMPLATE_FILE = "config.yaml-default"
DEFAULT_LOCAL_VERSION_FILE = "LocalVersion.yaml"
DEFAULT_UPDATE_CMD_FILE = "update.cmd"
DEFAULT_REMOTE_VERSION_URL = "https://cc.ncut.edu.tw/var/file/32/1032/img/1517/installer/RemoteVersion.yaml"
DEFAULT_SETUP_URL = "https://cc.ncut.edu.tw/var/file/32/1032/img/1517/installer/chklink_setup.exe"
APP_NAME = "chkLink"
APP_DISPLAY_NAME = "網頁失效連結掃描工具"
DEFAULT_APP_VERSION = "1.4"


def load_yaml(path: str) -> dict:
    """讀取 YAML 檔並回傳字典。"""
    yaml = YAML()
    with open(path, "r", encoding="utf-8") as file:
        data = yaml.load(file)
    return data or {}


def dump_yaml(path: str, data: dict) -> None:
    """以固定格式輸出 YAML 檔。"""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(path, "w", encoding="utf-8") as file:
        yaml.dump(data, file)


def default_setting() -> dict:
    """回傳內建預設設定。"""
    return {
        "layer": 3,
        "timeout": 8,
        "alt_must": "no",
        "check_http": "yes",
        "skip_visited": "yes",
        "rpt_folder": "",
        "remote_version_url": DEFAULT_REMOTE_VERSION_URL,
        "setup_url": DEFAULT_SETUP_URL,
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6,zh-CN;q=0.5,la;q=0.4",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Cookie": "_ga_SNR7NPLEYG=GS1.1.1651249603.1.0.1651250646.0; _ga_BGEHGPV3SB=GS1.1.1707539001.1.1.1707539323.0.0.0; _gid=GA1.3.1607128698.1707801742; _ga=GA1.1.381372473.1651249604; _ga_Q0EL30K2K5=GS1.1.1707801741.1.0.1707801770.0.0.0; _ga_54MVLT2EZN=GS1.1.1707843944.5.1.1707843969.0.0.0; __RequestVerificationToken_L05ldFNlcnZpY2Vz0=MrnqY4BqFXwyAR3uGWq5prQZPEwGWyzIJgIpuGFLyP8hqJ6eLKM9EWlC8NVA4MZqmyjtxmWT-9ZtzrO04NCTXcM_njimY7J0_WFWHlyWtzE1",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        },
        "avoid_urls": [
            "https://accessibility.moda.gov.tw/Applications/DetectLog/157716",
            "https://accessibility.moda.gov.tw/Home/Info/",
            "https://accessibility.moda.gov.tw/Download/Detail/1375?Category=52",
            "https://www.ndc.gov.tw/cp.aspx?n=32A75A78342B669D",
        ],
        "scan_urls": ["https://www.ncut.edu.tw/"],
    }


def ensure_local_version(
    version_file: str = DEFAULT_LOCAL_VERSION_FILE,
    app_version: str = DEFAULT_APP_VERSION,
) -> dict:
    """確保本機版本檔存在；若不存在則建立預設內容。"""
    if os.path.exists(version_file):
        data = load_yaml(version_file)
        if data.get("version"):
            return data

    data = {"version": app_version}
    dump_yaml(version_file, data)
    return data


def ensure_update_cmd(update_file: str = DEFAULT_UPDATE_CMD_FILE) -> None:
    """確保 update.cmd 存在；若不存在則建立預設內容。"""
    if os.path.exists(update_file):
        return

    lines = [
        "@echo off",
        "chcp 950 >nul",
        "setlocal",
        "set \"SETUP_PATH=%~1\"",
        "if \"%SETUP_PATH%\"==\"\" (",
        "    echo [錯誤] 缺少安裝程式路徑。",
        "    exit /b 1",
        ")",
        "if not exist \"%SETUP_PATH%\" (",
        "    echo [錯誤] 找不到安裝程式：%SETUP_PATH%",
        "    exit /b 1",
        ")",
        "echo [資訊] 準備啟動新版安裝程式...",
        "taskkill /f /im chklink.exe 2>nul",
        "timeout /t 1 /nobreak >nul",
        "start \"\" \"%SETUP_PATH%\"",
        "exit /b 0",
    ]
    with open(update_file, "w", encoding="cp950", newline="\r\n") as file:
        file.write("\r\n".join(lines) + "\r\n")


def create_config(cfg_file: str, template_file: str = DEFAULT_TEMPLATE_FILE) -> dict:
    """建立預設的 config.yaml。"""
    if os.path.exists(template_file):
        setting = load_yaml(template_file)
    else:
        setting = default_setting()
    dump_yaml(cfg_file, setting)
    return setting


def read_config(
    cfg_file: str,
    template_file: str = DEFAULT_TEMPLATE_FILE,
    on_missing=None,
) -> dict:
    """讀取 config.yaml，若不存在則建立。"""
    if os.path.exists(cfg_file):
        return load_yaml(cfg_file)

    setting = create_config(cfg_file, template_file=template_file)
    if on_missing is not None:
        on_missing()
    return setting


def normalize_setting(setting: dict, documents_dir: str) -> tuple[dict, bool]:
    """補齊必要設定並回傳是否有異動。"""
    updated = False

    if not setting.get("rpt_folder"):
        setting["rpt_folder"] = documents_dir
        updated = True
    elif not os.path.exists(setting["rpt_folder"]):
        setting["rpt_folder"] = documents_dir
        updated = True

    if not setting.get("check_http"):
        setting["check_http"] = "yes"
        updated = True

    if not setting.get("skip_visited"):
        setting["skip_visited"] = "yes"
        updated = True

    if not setting.get("remote_version_url"):
        setting["remote_version_url"] = DEFAULT_REMOTE_VERSION_URL
        updated = True

    if not setting.get("setup_url"):
        setting["setup_url"] = DEFAULT_SETUP_URL
        updated = True

    return setting, updated


def parse_positive_int(value, field_name: str, minimum: int = 1) -> int:
    """將輸入轉成正整數，失敗時拋出明確錯誤。"""
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} 必須是整數。") from exc
    if number < minimum:
        raise ValueError(f"{field_name} 必須大於或等於 {minimum}。")
    return number


def parse_yes_no(value, field_name: str) -> str:
    """驗證 yes/no 設定並回傳標準值。"""
    normalized = str(value).strip().lower()
    if normalized not in {"yes", "no"}:
        raise ValueError(f"{field_name} 只能是 yes 或 no。")
    return normalized


def normalize_headers(headers: dict) -> dict:
    """驗證並標準化標頭字典。"""
    if not isinstance(headers, dict):
        raise ValueError("請求的標頭必須是 key/value 對照。")

    normalized = {}
    for key, value in headers.items():
        header_name = str(key).strip()
        header_value = str(value).strip()
        if not header_name:
            raise ValueError("請求的標頭名稱不可空白。")
        if not header_value:
            raise ValueError(f"請求的標頭 {header_name} 缺少內容。")
        normalized[header_name] = header_value
    return normalized


def validate_url_list(urls: list[str], field_name: str, require_non_empty: bool = False) -> list[str]:
    """驗證網址清單，只接受 http/https。"""
    if urls is None:
        urls = []

    normalized = []
    for index, url in enumerate(urls, start=1):
        text = str(url).strip()
        if not text:
            continue
        parsed = urlparse(text)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"{field_name} 第 {index} 筆不是有效的 http/https 網址：{text}")
        normalized.append(text)

    if require_non_empty and not normalized:
        raise ValueError(f"{field_name} 至少要有一筆有效網址。")
    return normalized
