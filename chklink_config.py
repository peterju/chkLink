import copy
import os
import shutil
from urllib.parse import urlparse

from ruamel.yaml import YAML

APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = "data"
DEFAULT_TEMPLATE_FILE = "config.yaml-default"
DEFAULT_CONFIG_FILE = os.path.join(DATA_DIR, "config.yaml")
DEFAULT_LOCAL_VERSION_FILE = os.path.join(DATA_DIR, "LocalVersion.yaml")
DEFAULT_UPDATE_CMD_FILE = os.path.join(DATA_DIR, "update.cmd")
DEFAULT_VISITED_LINK_FILE = os.path.join(DATA_DIR, "visited_link.yaml")
DEFAULT_CONFIG_PATH = os.path.join(APP_BASE_DIR, DEFAULT_CONFIG_FILE)
DEFAULT_LOCAL_VERSION_PATH = os.path.join(APP_BASE_DIR, DEFAULT_LOCAL_VERSION_FILE)
DEFAULT_UPDATE_CMD_PATH = os.path.join(APP_BASE_DIR, DEFAULT_UPDATE_CMD_FILE)
DEFAULT_VISITED_LINK_PATH = os.path.join(APP_BASE_DIR, DEFAULT_VISITED_LINK_FILE)
DEFAULT_RELEASE_BASE_URL = "https://cc.ncut.edu.tw/var/file/32/1032/img/1517/"
DEFAULT_REMOTE_VERSION_FILE = "RemoteVersion.yaml"
DEFAULT_SETUP_FILE = "chklink_setup.exe"
DEFAULT_REMOTE_VERSION_URL = f"{DEFAULT_RELEASE_BASE_URL}{DEFAULT_REMOTE_VERSION_FILE}"
DEFAULT_SETUP_URL = f"{DEFAULT_RELEASE_BASE_URL}{DEFAULT_SETUP_FILE}"
APP_NAME = "chkLink"
APP_DISPLAY_NAME = "網頁失效連結掃描工具"
DEFAULT_APP_VERSION = "1.4"
DEFAULT_URL_NORMALIZATION = {
    "drop_fragment": "yes",
    "lowercase_scheme_host": "yes",
    "strip_default_port": "yes",
    "collapse_slashes": "yes",
    "strip_trailing_slash": "no",
    "sort_query_params": "no",
    "remove_query_params": [
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "msclkid",
    ],
}
DEFAULT_DOWNLOAD_LINK_RULES = {
    "extensions": [
        "7z",
        "csv",
        "doc",
        "docx",
        "exe",
        "gz",
        "iso",
        "jpg",
        "jpeg",
        "mp3",
        "mp4",
        "pdf",
        "png",
        "ppt",
        "pptx",
        "rar",
        "rtf",
        "tar",
        "tif",
        "tiff",
        "txt",
        "xls",
        "xlsx",
        "zip",
    ],
    "path_keywords": [
        "/download",
        "/downloads",
        "/attachment",
        "/attachments",
        "/file",
        "/files",
    ],
    "query_keys": ["download", "attachment", "file", "filename"],
    "query_value_keywords": ["download", "attachment"],
}
DEFAULT_SOFT_404_RULES = {
    "enabled": "yes",
    "title_keywords": [
        "404",
        "not found",
        "page not found",
        "找不到頁面",
        "查無此頁",
        "頁面不存在",
    ],
    "body_keywords": [
        "404",
        "not found",
        "page not found",
        "找不到頁面",
        "查無此頁",
        "頁面不存在",
        "查無資料",
        "無此資料",
        "很抱歉",
    ],
    "url_keywords": ["404", "notfound", "not-found", "missing", "error"],
    "max_text_length": 1200,
    "min_keyword_hits": 2,
}
DEFAULT_REDIRECT_RULES = {
    "classify_redirects": "yes",
    "suspicious_login_keywords": ["login", "signin", "sso", "auth"],
    "suspicious_error_keywords": ["404", "notfound", "not-found", "missing", "error"],
    "treat_cross_domain_as_warning": "no",
}

LEGACY_RUNTIME_FILES = {
    "config.yaml": DEFAULT_CONFIG_FILE,
    "LocalVersion.yaml": DEFAULT_LOCAL_VERSION_FILE,
    "update.cmd": DEFAULT_UPDATE_CMD_FILE,
    "visited_link.yaml": DEFAULT_VISITED_LINK_FILE,
}


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
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        yaml.dump(data, file)


def ensure_data_dir(base_dir: str = APP_BASE_DIR) -> str:
    """確保 data 目錄存在並回傳完整路徑。"""
    data_dir = os.path.join(base_dir, DATA_DIR)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def runtime_path(relative_path: str, base_dir: str = APP_BASE_DIR) -> str:
    """將執行期相對路徑轉成實際完整路徑。"""
    return os.path.join(base_dir, relative_path)


def migrate_legacy_runtime_files(base_dir: str = APP_BASE_DIR) -> None:
    """將舊版放在根目錄的執行期檔案搬到 data 目錄。"""
    ensure_data_dir(base_dir)
    for old_name, new_relative_path in LEGACY_RUNTIME_FILES.items():
        old_path = os.path.join(base_dir, old_name)
        new_path = runtime_path(new_relative_path, base_dir)
        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            shutil.move(old_path, new_path)


def default_setting() -> dict:
    """回傳內建預設設定。"""
    return {
        "layer": 3,
        "timeout": 8,
        "alt_must": "no",
        "check_http": "yes",
        "skip_visited": "yes",
        "rpt_folder": "",
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
        "url_normalization": copy.deepcopy(DEFAULT_URL_NORMALIZATION),
        "download_link_rules": copy.deepcopy(DEFAULT_DOWNLOAD_LINK_RULES),
        "soft_404_rules": copy.deepcopy(DEFAULT_SOFT_404_RULES),
        "redirect_rules": copy.deepcopy(DEFAULT_REDIRECT_RULES),
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
    """確保 data/update.cmd 存在；若不存在則建立預設內容。"""
    if os.path.exists(update_file):
        return

    os.makedirs(os.path.dirname(update_file) or ".", exist_ok=True)

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
    """建立預設的 data/config.yaml。"""
    os.makedirs(os.path.dirname(cfg_file) or ".", exist_ok=True)
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
    """讀取 data/config.yaml，若不存在則建立。"""
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

    updated = _merge_missing_defaults(setting, "url_normalization", DEFAULT_URL_NORMALIZATION) or updated
    updated = _merge_missing_defaults(setting, "download_link_rules", DEFAULT_DOWNLOAD_LINK_RULES) or updated
    updated = _merge_missing_defaults(setting, "soft_404_rules", DEFAULT_SOFT_404_RULES) or updated
    updated = _merge_missing_defaults(setting, "redirect_rules", DEFAULT_REDIRECT_RULES) or updated

    return setting, updated


def compose_release_url(base_url: str, file_name: str) -> str:
    """將基底網址與檔名組成下載網址。"""
    return str(base_url).rstrip("/") + "/" + str(file_name).lstrip("/")


def resolve_update_urls() -> tuple[str, str]:
    """依內建常數解析更新用網址。"""
    return (
        compose_release_url(DEFAULT_RELEASE_BASE_URL, DEFAULT_REMOTE_VERSION_FILE),
        compose_release_url(DEFAULT_RELEASE_BASE_URL, DEFAULT_SETUP_FILE),
    )


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


def normalize_string_list(values, field_name: str, lowercase: bool = False) -> list[str]:
    """驗證字串清單，可選擇統一轉成小寫。"""
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError(f"{field_name} 必須是清單。")

    normalized = []
    for index, value in enumerate(values, start=1):
        text = str(value).strip()
        if not text:
            continue
        normalized.append(text.lower() if lowercase else text)
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


def resolve_scan_advanced_settings(setting: dict) -> dict:
    """解析掃描核心的進階設定。"""
    url_normalization = setting.get("url_normalization") or {}
    download_link_rules = setting.get("download_link_rules") or {}
    soft_404_rules = setting.get("soft_404_rules") or {}
    redirect_rules = setting.get("redirect_rules") or {}

    return {
        "url_normalization": {
            "drop_fragment": parse_yes_no(
                url_normalization.get("drop_fragment", DEFAULT_URL_NORMALIZATION["drop_fragment"]),
                "url_normalization.drop_fragment",
            ),
            "lowercase_scheme_host": parse_yes_no(
                url_normalization.get("lowercase_scheme_host", DEFAULT_URL_NORMALIZATION["lowercase_scheme_host"]),
                "url_normalization.lowercase_scheme_host",
            ),
            "strip_default_port": parse_yes_no(
                url_normalization.get("strip_default_port", DEFAULT_URL_NORMALIZATION["strip_default_port"]),
                "url_normalization.strip_default_port",
            ),
            "collapse_slashes": parse_yes_no(
                url_normalization.get("collapse_slashes", DEFAULT_URL_NORMALIZATION["collapse_slashes"]),
                "url_normalization.collapse_slashes",
            ),
            "strip_trailing_slash": parse_yes_no(
                url_normalization.get("strip_trailing_slash", DEFAULT_URL_NORMALIZATION["strip_trailing_slash"]),
                "url_normalization.strip_trailing_slash",
            ),
            "sort_query_params": parse_yes_no(
                url_normalization.get("sort_query_params", DEFAULT_URL_NORMALIZATION["sort_query_params"]),
                "url_normalization.sort_query_params",
            ),
            "remove_query_params": normalize_string_list(
                url_normalization.get("remove_query_params", DEFAULT_URL_NORMALIZATION["remove_query_params"]),
                "url_normalization.remove_query_params",
                lowercase=True,
            ),
        },
        "download_link_rules": {
            "extensions": normalize_string_list(
                download_link_rules.get("extensions", DEFAULT_DOWNLOAD_LINK_RULES["extensions"]),
                "download_link_rules.extensions",
                lowercase=True,
            ),
            "path_keywords": normalize_string_list(
                download_link_rules.get("path_keywords", DEFAULT_DOWNLOAD_LINK_RULES["path_keywords"]),
                "download_link_rules.path_keywords",
                lowercase=True,
            ),
            "query_keys": normalize_string_list(
                download_link_rules.get("query_keys", DEFAULT_DOWNLOAD_LINK_RULES["query_keys"]),
                "download_link_rules.query_keys",
                lowercase=True,
            ),
            "query_value_keywords": normalize_string_list(
                download_link_rules.get("query_value_keywords", DEFAULT_DOWNLOAD_LINK_RULES["query_value_keywords"]),
                "download_link_rules.query_value_keywords",
                lowercase=True,
            ),
        },
        "soft_404_rules": {
            "enabled": parse_yes_no(
                soft_404_rules.get("enabled", DEFAULT_SOFT_404_RULES["enabled"]),
                "soft_404_rules.enabled",
            ),
            "title_keywords": normalize_string_list(
                soft_404_rules.get("title_keywords", DEFAULT_SOFT_404_RULES["title_keywords"]),
                "soft_404_rules.title_keywords",
                lowercase=True,
            ),
            "body_keywords": normalize_string_list(
                soft_404_rules.get("body_keywords", DEFAULT_SOFT_404_RULES["body_keywords"]),
                "soft_404_rules.body_keywords",
                lowercase=True,
            ),
            "url_keywords": normalize_string_list(
                soft_404_rules.get("url_keywords", DEFAULT_SOFT_404_RULES["url_keywords"]),
                "soft_404_rules.url_keywords",
                lowercase=True,
            ),
            "max_text_length": parse_positive_int(
                soft_404_rules.get("max_text_length", DEFAULT_SOFT_404_RULES["max_text_length"]),
                "soft_404_rules.max_text_length",
            ),
            "min_keyword_hits": parse_positive_int(
                soft_404_rules.get("min_keyword_hits", DEFAULT_SOFT_404_RULES["min_keyword_hits"]),
                "soft_404_rules.min_keyword_hits",
            ),
        },
        "redirect_rules": {
            "classify_redirects": parse_yes_no(
                redirect_rules.get("classify_redirects", DEFAULT_REDIRECT_RULES["classify_redirects"]),
                "redirect_rules.classify_redirects",
            ),
            "suspicious_login_keywords": normalize_string_list(
                redirect_rules.get(
                    "suspicious_login_keywords",
                    DEFAULT_REDIRECT_RULES["suspicious_login_keywords"],
                ),
                "redirect_rules.suspicious_login_keywords",
                lowercase=True,
            ),
            "suspicious_error_keywords": normalize_string_list(
                redirect_rules.get(
                    "suspicious_error_keywords",
                    DEFAULT_REDIRECT_RULES["suspicious_error_keywords"],
                ),
                "redirect_rules.suspicious_error_keywords",
                lowercase=True,
            ),
            "treat_cross_domain_as_warning": parse_yes_no(
                redirect_rules.get(
                    "treat_cross_domain_as_warning",
                    DEFAULT_REDIRECT_RULES["treat_cross_domain_as_warning"],
                ),
                "redirect_rules.treat_cross_domain_as_warning",
            ),
        },
    }


def _merge_missing_defaults(setting: dict, key: str, default_value: dict) -> bool:
    """只補齊缺少的巢狀預設值，不覆蓋既有內容。"""
    current_value = setting.get(key)
    if current_value is None:
        setting[key] = copy.deepcopy(default_value)
        return True
    if not isinstance(current_value, dict):
        return False

    updated = False
    for child_key, child_default in default_value.items():
        if child_key not in current_value or current_value[child_key] is None:
            current_value[child_key] = copy.deepcopy(child_default)
            updated = True
    return updated
