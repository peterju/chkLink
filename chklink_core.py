import logging
import os
import re
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import openpyxl
import requests
from bs4 import BeautifulSoup, UnicodeDammit
from openpyxl.styles import Alignment, Font, PatternFill
from ruamel.yaml import YAML
from selenium import webdriver
from selenium.common.exceptions import NoSuchDriverException, WebDriverException

EmitFunc = Callable[[str, str], None]
StopFunc = Callable[[], bool]
EMPTY_CONTENT_MARKER = "200 (內容為空)"
SKIPPED_MARKER = "200 (避免檢查的網址)"
HTTP_WARNING_MARKER = "且使用 http 協定並不安全"
SPA_SHELL_MARKER = "200 (疑似前端框架頁面)"


@dataclass
class ScanOptions:
    """掃描流程需要的設定參數。"""

    headers: dict
    avoid_urls: list[str]
    timeout: int
    alt_must: bool
    check_http: bool
    skip_visited: bool = True


@dataclass
class ScanContext:
    """掃描期間共用的執行環境與狀態。"""

    logger: logging.Logger
    visited_link: dict
    browser: webdriver.Chrome
    emit: EmitFunc | None = None
    should_stop: StopFunc | None = None

    def push(self, level: str, message: str) -> None:
        """同時寫入 logger，必要時也回呼到 UI。"""
        if level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)
        if self.emit is not None:
            self.emit(level, message)

    def stopped(self) -> bool:
        """回傳目前是否已被要求停止掃描。"""
        return self.should_stop is not None and self.should_stop()


def create_webdriver() -> webdriver.Chrome:
    """建立 Selenium Chrome 瀏覽器實例。"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--log-level=3")
    try:
        browser = webdriver.Chrome(options=chrome_options)
        browser.implicitly_wait(20)
        return browser
    except (NoSuchDriverException, WebDriverException) as exc:
        raise RuntimeError(f"Selenium Manager 啟動失敗：{exc}") from exc


def create_logger(log_folder: str, filename: str, with_console: bool = False) -> logging.Logger:
    """建立 logger，必要時同步輸出到 console。"""
    logger = logging.getLogger(filename)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter(
        "[%(asctime)s - %(levelname)s] %(message)s",
        datefmt="%Y%m%d %H:%M:%S",
    )

    if with_console:
        console_handle = logging.StreamHandler()
        console_handle.setLevel(logging.INFO)
        console_handle.setFormatter(formatter)
        logger.addHandler(console_handle)

    logname = os.path.join(log_folder, f"{filename}.log")
    file_handle = logging.FileHandler(logname, "w", "utf-8")
    file_handle.setLevel(logging.INFO)
    file_handle.setFormatter(formatter)
    logger.addHandler(file_handle)
    return logger


def close_logger(logger: logging.Logger) -> None:
    """關閉並移除 logger 的所有 handlers。"""
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def load_visited_link(visited_link_file: str) -> dict:
    """載入已檢查過且成功的連結清單。"""
    if os.path.exists(visited_link_file):
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.indent(mapping=2, sequence=4, offset=2)
        with open(visited_link_file, "r", encoding="utf-8") as file:
            data = yaml.load(file)
            return data or {}
    return {}


def save_visited_link(visited_link_file: str, visited_link: dict) -> None:
    """儲存已檢查過且成功的連結清單。"""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(visited_link_file, "w", encoding="utf-8") as file:
        for key, value in visited_link.items():
            if "200" in value:
                yaml.dump({key: value}, file)


def _requests_get(
    url: str,
    headers: dict,
    timeout: int,
    allow_redirects: bool = True,
    referer: str | None = None,
) -> requests.Response:
    """依協定包裝 requests.get。"""
    request_headers = dict(headers)
    if referer:
        request_headers["Referer"] = referer
    protocol = urlparse(url).scheme
    if protocol == "https":
        return requests.get(url, headers=request_headers, timeout=timeout, allow_redirects=allow_redirects)
    return requests.get(
        url,
        headers=request_headers,
        timeout=timeout,
        allow_redirects=allow_redirects,
        verify=False,
    )


def _is_problem_status(status: str) -> bool:
    """判斷狀態是否應被視為錯誤或警告。"""
    return "200" not in status or EMPTY_CONTENT_MARKER in status


def _is_html_like_url(url: str) -> bool:
    """判斷網址是否看起來像可繼續爬的網頁。"""
    match = re.search(r".*\.\w{2,4}$", url)
    if not match:
        return True
    return url.endswith(("html", "htm", "php", "asp", "aspx", "jsp", "tw", "com"))


def _is_local_http_target(url: str) -> bool:
    """判斷是否為本機測試用的 HTTP 網址。"""
    hostname = (urlparse(url).hostname or "").lower()
    return hostname in {"localhost", "127.0.0.1"}


def _normalized_hostname(url: str) -> str:
    """取得標準化後的主機名稱。"""
    return (urlparse(url).hostname or "").lower()


def _should_fallback_to_browser(status: str) -> bool:
    """判斷目前狀態是否需要改用 Selenium 補驗。"""
    return "連線逾時" in status or "無法連線至此網頁" in status


def _looks_like_spa_shell(response: requests.Response) -> bool:
    """判斷 HTML 是否看起來只是 Vue/React 類前端框架的殼。"""
    content_type = (response.headers.get("Content-Type") or "").lower()
    if "html" not in content_type:
        return False

    dammit = UnicodeDammit(response.content, ["utf-8", "latin-1", "iso-8859-1", "windows-1251"])
    markup = dammit.unicode_markup or ""
    if not markup.strip():
        return True

    soup = BeautifulSoup(markup, "lxml")
    body = soup.body or soup
    visible_text = body.get_text(" ", strip=True)
    visible_text = re.sub(r"\s+", " ", visible_text)
    script_count = len(soup.find_all("script"))
    has_mount_node = soup.select_one("#app, #root, #__next, #__nuxt, [data-reactroot], [data-react-checksum]") is not None
    has_framework_hint = any(
        token in markup.lower()
        for token in ("__vite__", "data-server-rendered", "id=\"app\"", "id=\"root\"", "id=\"__next\"", "id=\"__nuxt\"")
    )
    noscript_text = " ".join(tag.get_text(" ", strip=True).lower() for tag in soup.find_all("noscript"))
    asks_for_js = any(
        phrase in noscript_text
        for phrase in ("enable javascript", "javascript", "啟用 javascript", "需啟用 javascript", "請開啟 javascript")
    )

    return len(visible_text) <= 40 and (has_mount_node or has_framework_hint or asks_for_js or script_count >= 3)


def _browser_fetch_status(full_url: str, context: ScanContext, original_status: str) -> str:
    """改用瀏覽器嘗試開啟網址，補強 requests 無法判斷的情況。"""
    try:
        context.browser.get(full_url)
        page_source = context.browser.page_source or ""
        body_text = page_source.strip()
        if not body_text:
            return f"200 改以瀏覽器自動化測試開啟成功，但內容為空，原訊息：{original_status}"
        return f"200 改以瀏覽器自動化測試開啟成功，原訊息：{original_status}"
    except WebDriverException:
        return original_status


def check_link(base_url: str, link: str, link_text: str, options: ScanOptions, context: ScanContext) -> str:
    """檢查單一連結並回傳狀態字串。"""
    if link.startswith("http"):
        full_url = link.strip()
    else:
        full_url = urljoin(base_url, link).strip()

    if full_url in options.avoid_urls:
        status = SKIPPED_MARKER
    elif full_url in context.visited_link and options.skip_visited:
        status = f"{context.visited_link[full_url]} (已檢查過網址)"
    else:
        protocol = urlparse(full_url).scheme
        try:
            response = _requests_get(full_url, options.headers, options.timeout, allow_redirects=True, referer=base_url)
            status = str(response.status_code)
            content_length = len(response.content)
            real_url = response.url
            domain1 = urlparse(full_url).netloc
            domain2 = urlparse(real_url).netloc
            if status == "200" and domain1 != domain2:
                response = _requests_get(
                    full_url,
                    options.headers,
                    options.timeout,
                    allow_redirects=False,
                    referer=base_url,
                )
                status = f"200 重定向：{response.status_code} 到 {real_url}"
            if status == "200" and content_length == 0:
                status = EMPTY_CONTENT_MARKER
            elif status == "200" and _looks_like_spa_shell(response):
                status = SPA_SHELL_MARKER
        except requests.exceptions.ConnectTimeout as exc:
            status = f"連線逾時：{link}  錯誤訊息：{exc}"
        except requests.exceptions.ConnectionError as exc:
            status = f"無法連線至此網頁：{link}  錯誤訊息：{exc}"
        except requests.exceptions.Timeout as exc:
            status = f"連線逾時：{link}  錯誤訊息：{exc}"
        except requests.exceptions.MissingSchema as exc:
            status = f"連結缺少協定：{link}  錯誤訊息：{exc}"
        except requests.exceptions.TooManyRedirects as exc:
            status = f"重新導向次數過多：{link}  錯誤訊息：{exc}"
        except requests.exceptions.SSLError as exc:
            status = f"SSL 錯誤或憑證不正確：{link}  錯誤訊息：{exc}"
        except requests.exceptions.RequestException as exc:
            status = f"無法取得此網頁內容：{link}  錯誤訊息：{exc}"
        except requests.exceptions.HTTPError as exc:
            status = f"HTTP 錯誤：{link}  錯誤訊息：{exc}"
        except Exception as exc:
            status = f"其它錯誤：{link}  錯誤訊息：{exc}"

        if _should_fallback_to_browser(status):
            status = _browser_fetch_status(full_url, context, status)
        elif status == SPA_SHELL_MARKER:
            status = _browser_fetch_status(full_url, context, status)

        if status == "403":
            status = f"{status} 請求被拒絕"
        elif status == "404":
            status = f"{status} 請求失敗"
        elif status == "410":
            status = f"{status} 請求的資源已經不存在"
        elif status == "500":
            status = f"{status} 伺服器錯誤"
        elif protocol == "http" and not _is_local_http_target(full_url):
            status = f"{status} {HTTP_WARNING_MARKER}"

        context.visited_link[full_url] = status

    message = f"檢查: {link} ... 狀態: {status} ... 文字: {link_text}"
    if "200" in status:
        if HTTP_WARNING_MARKER in status or EMPTY_CONTENT_MARKER in status:
            context.push("warning", message)
        else:
            context.push("info", message)
    else:
        context.push("error", message)
    return status


def get_links(url: str, options: ScanOptions, context: ScanContext) -> tuple[list, list, list, list]:
    """取得頁面中的內部連結、外部連結、缺少 alt 的圖片與 HTTP 連結。"""
    try:
        domain = _normalized_hostname(url)
        response = _requests_get(url.strip(), options.headers, options.timeout, allow_redirects=True, referer=url)
        real_url = response.url
        real_domain = _normalized_hostname(real_url)
        if domain != real_domain:
            return ([], [], [], [])

        dammit = UnicodeDammit(response.content, ["utf-8", "latin-1", "iso-8859-1", "windows-1251"])
        soup = BeautifulSoup(dammit.unicode_markup, "lxml")
        result = soup.find("meta", attrs={"http-equiv": "refresh"})
        if result:
            _wait, client_url = result["content"].split(";")
            if client_url.strip().lower().startswith("url="):
                client_url = urljoin(url, client_url.strip()[4:])
            response = _requests_get(client_url, options.headers, options.timeout, allow_redirects=True, referer=url)
            dammit = UnicodeDammit(response.content, ["utf-8", "latin-1", "iso-8859-1", "windows-1251"])
            soup = BeautifulSoup(dammit.unicode_markup, "lxml")
            context.push("info", f"網頁於前端重新導向至：{client_url}")

        all_links = []
        internal_links, external_links, no_alt_links, http_links = [], [], [], []

        for tag in soup.find_all(href=True):
            link = tag.get("href").strip()
            link_text = tag.text.strip() or link.split("/")[-1]
            all_links.append((link, link_text))

        for tag in soup.find_all(src=True):
            link = tag.get("src").strip()
            link_text = tag.get("alt", "").strip() or link.split("/")[-1]
            all_links.append((link, link_text))

        if options.alt_must:
            no_alt_links = [
                (tag.get("src"), tag.get("src").split("/")[-1]) for tag in soup.find_all("img", alt=False)
            ]

        for link, link_text in list(set(all_links)):
            absolute_link = urljoin(url, link).strip()
            link_domain = _normalized_hostname(absolute_link)
            scheme = urlparse(absolute_link).scheme
            if link.startswith(("#", "javascript", "mailto", "data:image")):
                continue
            if scheme not in ("http", "https"):
                continue
            if link_domain == domain:
                internal_links.append((absolute_link, link_text))
                if absolute_link.startswith("http://") and options.check_http and not _is_local_http_target(absolute_link):
                    http_links.append((absolute_link, link_text))
            elif link.startswith(("http", "//")):
                external_links.append((absolute_link, link_text))
                if absolute_link.startswith("http://") and options.check_http and not _is_local_http_target(absolute_link):
                    http_links.append((absolute_link, link_text))
            else:
                internal_links.append((absolute_link, link_text))
                if absolute_link.startswith("http://") and options.check_http and not _is_local_http_target(absolute_link):
                    http_links.append((absolute_link, link_text))

        return internal_links, external_links, no_alt_links, http_links
    except Exception as exc:
        message = f"無法取得此網頁內容：{url}  錯誤訊息：{exc}"
        context.push("error", message)
        return ([(url, f"無法取得此網頁內容：{exc}")], [], [], [])


def scan_site(start_url: str, depth_limit: int, options: ScanOptions, context: ScanContext) -> list[dict]:
    """使用佇列方式掃描指定網站並回傳結果。"""
    visited_url = set()
    queue = deque([(start_url, 0)])
    queued_url = {start_url}
    all_err_links = []
    start_domain = _normalized_hostname(start_url)

    while queue:
        if context.stopped():
            break

        url, current_depth = queue.popleft()
        queued_url.discard(url)
        if url in options.avoid_urls:
            continue
        if not _is_html_like_url(url):
            continue
        if url in visited_url or current_depth > depth_limit:
            continue

        context.push("info", f"第 {current_depth} 層連結： {url}")
        visited_url.add(url)

        internal_links, external_links, no_alt_links, http_links = get_links(url, options, context)
        if internal_links:
            context.push("info", "內部連結：" + ", ".join([link for link, _ in internal_links]))
        if external_links:
            context.push("info", "外部連結：" + ", ".join([link for link, _ in external_links]))
        if no_alt_links:
            context.push("info", "沒有 alt 屬性的連結：" + ", ".join([link for link, _ in no_alt_links]))
        if http_links:
            context.push("info", "HTTP 連結：" + ", ".join([link for link, _ in http_links]))
        internal_statuses = []
        for link, link_text in internal_links:
            if context.stopped():
                break
            status = check_link(url, link, link_text, options, context)
            internal_statuses.append((link, status, link_text))

        error_internal_links = [item for item in internal_statuses if _is_problem_status(item[1])]
        error_external_links = []
        error_links = list(set(error_internal_links + error_external_links))

        if error_links:
            context.push("error", "錯誤連結：" + ", ".join([link for link, _, _ in error_links]))

        if error_links or no_alt_links or http_links:
            all_err_links.append(
                {
                    "depth": current_depth,
                    "url": url,
                    "error_links": error_links,
                    "no_alt_links": no_alt_links,
                    "http_links": http_links,
                }
            )

        if current_depth >= depth_limit:
            continue

        error_internal_set = {(link, link_text) for link, _, link_text in error_internal_links}
        for link, link_text in internal_links:
            if (link, link_text) in error_internal_set:
                continue
            absolute_link = urljoin(url, link).strip()
            if _normalized_hostname(absolute_link) != start_domain:
                continue
            if absolute_link not in visited_url and absolute_link not in queued_url:
                queue.append((absolute_link, current_depth + 1))
                queued_url.add(absolute_link)

    return all_err_links


def write_report(report_folder: str, filename: str, result: list[dict], include_http_links: bool) -> None:
    """將掃描結果寫入 Excel 報告。"""
    xlsx_name = os.path.join(report_folder, f"{filename}.xlsx")
    workbook = openpyxl.Workbook()
    sheet = workbook.worksheets[0]
    sheet.append(("層數", "網頁", "錯誤連結", "連結文字", "狀態碼或錯誤訊息"))

    for column in range(1, sheet.max_column + 1):
        sheet.cell(1, column).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        sheet.cell(1, column).font = Font(bold=True)
    sheet.row_dimensions[1].height = 20

    for rec in sorted(result, key=lambda item: (item["depth"], item["url"])):
        for link, status, link_text in rec["error_links"]:
            sheet.append([rec["depth"], rec["url"], link, link_text, status])
        for link, link_text in rec["no_alt_links"]:
            sheet.append([rec["depth"], rec["url"], link, link_text, "圖片沒有 alt 屬性"])
        if include_http_links:
            for link, link_text in rec.get("http_links", []):
                sheet.append([rec["depth"], rec["url"], link, link_text, f"使用 http 協定並不安全"])

    column_widths = {"A": 8, "B": 60, "C": 70, "D": 35, "E": 70}
    for col, width in column_widths.items():
        sheet.column_dimensions[col].width = width

    for row in range(1, sheet.max_row + 1):
        sheet.cell(row, 1).alignment = Alignment(horizontal="center", vertical="center")

    for row in range(2, sheet.max_row + 1):
        sheet.cell(row, 2).style = "Hyperlink"
        sheet.cell(row, 2).hyperlink = sheet.cell(row, 2).value
        sheet.cell(row, 2).alignment = Alignment(vertical="center", wrap_text=True)

        sheet.cell(row, 3).style = "Hyperlink"
        if not sheet.cell(row, 3).value.startswith(("http", "//")):
            sheet.cell(row, 3).hyperlink = urljoin(sheet.cell(row, 2).value, sheet.cell(row, 3).value)
        else:
            sheet.cell(row, 3).hyperlink = sheet.cell(row, 3).value
        sheet.cell(row, 3).alignment = Alignment(vertical="center", wrap_text=True)
        sheet.cell(row, 4).alignment = Alignment(vertical="center", wrap_text=True)
        sheet.cell(row, 5).alignment = Alignment(vertical="center", wrap_text=True)

        for column in range(1, sheet.max_column + 1):
            sheet.cell(row, column).fill = (
                PatternFill(start_color="cfe2f3", end_color="cfe2f3", fill_type="solid")
                if row % 2 == 0
                else PatternFill(fill_type=None)
            )

    sheet.freeze_panes = sheet["A2"]
    workbook.save(xlsx_name)
