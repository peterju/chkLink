# 網頁失效連結掃描工具

這是一套用來掃描網站失效連結的工具，提供 GUI 與 CLI 兩種使用方式。它會遞迴掃描站內頁面、驗證內部連結、列出外部連結、檢查圖片是否缺少 `alt`，並輸出 Excel 報告與 log 紀錄，方便網站維護人員定期盤點問題。

它使用 Python 開發，再使用 nuitka 打包，最後使用 Inno Setup 製作安裝檔，再用 SignTool 使用自然人憑證加簽。

## 快速導覽

- 想先知道這個工具做什麼：看「專案用途」與「掃描範圍定義」
- 想直接跑起來：看「執行方式」
- 想理解 GUI / CLI 掃描邏輯：看「GUI 重要邏輯」
- 想調整掃描設定：看「設定檔說明」
- 想改版本、編譯、打包與更新：看「版本號來源」與「正式發佈與升級流程」
- 想公開 repo 或交接維護：看「公開 Repo 前的注意事項」、「已知限制」與根目錄 [AGENTS.md](AGENTS.md)

## 先看這裡

如果你是第一次接手這個專案，建議先掌握下面 4 件事：

1. 主產品是 GUI，CLI 是低曝光輔助入口。
2. 掃描核心共用在 [chklink_core.py](chklink_core.py)，不要分別在 GUI / CLI 內重複改邏輯。
3. 執行中的版本號唯一來源是 [chklink_config.py](chklink_config.py) 的 `DEFAULT_APP_VERSION`。
4. 組織內部更新來源與 GitHub Release 是兩條分開的發佈線，不要把 `make_github_release.cmd` 產物誤當成 GUI 預設更新來源。

## 專案用途

- 掃描網站中的內部連結是否可正常開啟
- 列出頁面上的外部連結，不對外站發送連通性驗證請求
- 額外標示不安全的 `http://` 連結
- 檢查圖片是否缺少 `alt` 屬性
- 產生 `.xlsx` 報告與 `.log` 紀錄
- 支援以 `standalone + Inno Setup` 方式封裝成安裝程式

## 掃描範圍定義

目前專案採用的原則是：

- 只對起始網址所屬站台的內部連結做有效性驗證
- 只對內部連結繼續往下遞迴掃描
- 外部連結只做列出，不做請求驗證
- 外部連結不算錯誤連結，也不會因為重複出現在多頁而被反覆請求
- 但外部連結若使用 `http://`，仍會列為內容維護提醒，方便後續人工確認是否可改成 `https://`

這樣做的目的，是讓工具聚焦在「本站內容維護」而不是替外站做健康檢查，也可避免同一個外部首頁或共用外站資源被重複驗證很多次。

## 主要檔案

- `chklink.py`：GUI 主程式，含掃描、設定、更新與報表功能
- `chklink_cli.py`：CLI 主程式
- `data\config.yaml`：實際使用的設定檔
- `config.yaml-default`：預設設定樣板
- `data\visited_link.yaml`：已檢查過且回應正常的連結快取
- `run.cmd`：啟動 GUI
- `make_exec.cmd`：第 1 階段，編譯 GUI / CLI 並產生 `RemoteVersion.yaml`
- `make_sign_app.cmd`：第 2 階段，對 GUI / CLI 執行檔加簽
- `make_setup.cmd`：第 3 階段，建立對應版本的 installer
- `make_sign_setup.cmd`：第 4 階段，對 installer 加簽
- `make_sha256.cmd`：可選步驟，為 installer 與 `RemoteVersion.yaml` 產生 `SHA256.txt`
- `make_github_release.cmd`：整理 GitHub Release 用的版本化檔名與 SHA256 檔案
- `menu.cmd`：提供 `1 / 2 / 3 / 4 / 5 / 6` 的互動式建置選單
- `build_setup.ps1`：由 `make_setup.cmd` 呼叫，用來產生 Inno Setup 安裝程式
- `installer_template.iss`：Inno Setup 穩定模板
- `data\update.cmd`：啟動新版安裝程式用的批次檔
- `sign_files.ps1`：由 `make_sign_app.cmd` 與 `make_sign_setup.cmd` 呼叫，用來分階段簽章

## 使用與維護地圖

- 日常使用者：
  - 先看「執行方式」
  - 再看「設定檔說明」
- 掃描邏輯維護者：
  - 先看「GUI 重要邏輯」
  - 再看 [chklink_core.py](chklink_core.py)
- 打包與發佈維護者：
  - 先看「正式發佈與升級流程」
  - 再看 [build_setup.ps1](build_setup.ps1)、[installer_template.iss](installer_template.iss)、[sign_files.ps1](sign_files.ps1)

## 角色與版本更新的比對來源

- GUI 是主要入口，負責一般使用者操作、更新檢查、掃描與報表。
- CLI 共用同一套掃描核心，但主要用途是排程、自動化與除錯。
- 掃描邏輯真相來源在 [chklink_core.py](chklink_core.py)。
- 版本號真相來源在 [chklink_config.py](chklink_config.py) 的 `DEFAULT_APP_VERSION`。
- 版本更新的比對來源是 `installer\<版本>\RemoteVersion.yaml`。
- 使用者執行期資料是 `data\config.yaml` 與 `data\visited_link.yaml`。
- `data\update.cmd` 是程式持有的更新輔助檔，不是使用者設定檔。

## 執行方式

GUI：

```powershell
python chklink.py
```

或：

```powershell
run.cmd
```

CLI：

```powershell
python chklink_cli.py
```

## GUI 重要邏輯

### 1. 啟動與初始化

GUI 啟動時會：

- 若缺少 `data\config.yaml`，會在本機建立預設設定檔
- 讀取 `data\config.yaml`
- 若存在則載入 `data\visited_link.yaml`；此檔為成功連結快取，通常會在完成一次掃描並儲存結果後建立或更新

CLI 版 `chklink_cli.py` 不參與 Inno Setup 安裝版的更新流程；若缺少 `data\config.yaml`，仍會依既有邏輯在本機建立 fallback 檔案。

目前 installer 會一併安裝 GUI 與 CLI 執行檔；其中 CLI 只會放在安裝目錄內，不會額外建立桌面或開始功能表捷徑。
發佈產物會依版本號輸出到 `installer\<版本>\`，例如 `installer\1.4.0\chklink_setup.exe` 與 `installer\1.4.0\RemoteVersion.yaml`。
目前建置流程拆成 4 個固定步驟；若需要簽章，請先執行 `make_sign_app.cmd`，在建立 installer 後再執行 `make_sign_setup.cmd`。

若你是新維護者，或是要讓其他 AI / agent 工具接手這個專案，請另外參考根目錄的 [AGENTS.md](AGENTS.md)。

### 2. 掃描流程

按下「掃描」後，`analysis_func()` 會啟動背景執行緒，真正的掃描工作由 `queued_link_check()` 處理。核心流程如下：

1. 讀取 GUI 上目前設定的 `headers`、`avoid_urls`、起始網址與深度。
   - 這一步會先驗證數字欄位、網址清單與標頭格式
2. 啟動 headless Chrome，並透過 Selenium Manager 取得可用的 driver。
3. 使用 `deque` 當作佇列，從起始網址開始做廣度優先掃描。
4. 每個頁面先經過 `get_links()` 解析：
   - 擷取 `href` 與 `src`
   - 分成內部連結、外部連結、缺少 `alt` 的圖片、`http://` 連結
   - 若頁面有 `meta refresh`，會再追一次重新導向後的頁面內容
5. 只有內部連結會再由共用核心 `check_link()` 驗證：
   - 先用 `requests` 發送請求
   - 會參考 `Content-Type` 與 `Content-Disposition`，補強下載檔與非 HTML 內容判定
   - 若出現「連線逾時」或「無法連線至此網頁」，會再用 Selenium 實際打開頁面補驗
   - 若 `requests` 回應 `200`，但 HTML 明顯只是 Vue.js、React、Next.js、Nuxt 這類前端框架的初始殼頁，也會改用 Selenium 補驗
   - 會先做 URL 正規化，避免 fragment、預設 port 與常見追蹤參數造成重複掃描
   - 若判定為下載型連結，仍會檢查可否開啟，但不會再當成 HTML 頁面繼續往下爬
   - 若原始網址與實際落點不同，會標示重定向類型，並額外辨識是否疑似導向登入頁、錯誤頁或站外
   - 若回應 `200` 但內容與網址特徵像是找不到頁面，會標示為疑似 soft-404
   - 若回應 `200` 但內容長度為 0，會標示為「內容為空」
6. 外部連結只會被列出，不會進行有效性驗證，也不會往下遞迴；但若外部連結使用 `http://`，仍會列成提醒。
7. 將錯誤連結、缺少 `alt` 的圖片、以及 `http://` 連結整理成記錄。
8. 請求會依設定做 retry、backoff 與同網域節流，降低暫時性誤判與對目標站的壓力。
9. 掃描完成後呼叫共用核心輸出 Excel 報告，並把成功的連結存回 `data\visited_link.yaml`。

### 3. 已檢查連結快取

- GUI 上有「跳過已檢查過的網址」選項，CLI 也會讀取同一個 `skip_visited` 設定。
- 若啟用，程式會優先查 `data\visited_link.yaml`，並以正規化後的 URL 當 key，避免對同一頁不同寫法重複發送請求。
- 只有包含 `200` 的狀態會被寫回快取。
- `data\visited_link.yaml` 不一定會在首次啟動時出現；通常是在實際掃描完成並寫回快取後才建立。

### 4. `http://` 判定規則

- 若 `check_http=yes`，會將 `http://` 連結列入報表與警告。
- 這個提醒同時包含內部與外部連結；外部 `http://` 的目的不是驗證外站，而是提醒本站頁面可能仍引用過時或較不安全的網址。
- `localhost` 與 `127.0.0.1` 例外，不視為不安全連結，避免影響本機測試。

### 5. Selenium 補驗觸發條件

GUI 與 CLI 目前已統一，只有在下列情況才會改用 Selenium 補驗：

- `requests` 判定為「連線逾時」
- `requests` 判定為「無法連線至此網頁」
- `requests` 回應 `200`，但 HTML 看起來只是前端框架殼頁

所謂「前端框架殼頁」，目前會參考下列跡象綜合判斷：

- 頁面幾乎沒有可見文字
- HTML 中出現 `#app`、`#root`、`#__next`、`#__nuxt`、`data-reactroot` 之類常見掛載節點
- 頁面有多個 script，但正文內容極少
- `noscript` 提示要求啟用 JavaScript

這是為了避免 Vue.js、React、Next.js、Nuxt 這類網站在 `requests` 看起來像空頁，卻其實需要瀏覽器執行 JavaScript 才能完成渲染，進而被誤判為異常。

下列情況目前不會自動改用 Selenium 補驗，而是直接採用 `requests` 的結果：

- `403`
- `404`
- `410`
- `500`
- `SSL 錯誤`
- `重新導向次數過多`
- `回應 200 但內容為空`

### 6. 報表輸出

`report()` 會輸出 `.xlsx`，欄位包含：

- 層數
- 網頁
- 錯誤連結
- 連結文字
- 狀態碼或錯誤訊息

此外：

- `http://` 連結可依設定列入報表
- 缺少 `alt` 的圖片也會列成獨立紀錄
- Excel 會自動加上超連結樣式與欄寬

## 設定檔說明

`data\config.yaml` 主要欄位如下：

- `layer`：掃描深度
- `timeout`：逾時秒數
- `alt_must`：是否檢查圖片 `alt`
- `check_http`：是否標示 `http://` 連結
- `skip_visited`：是否略過已成功檢查過的網址
- `rpt_folder`：報告輸出資料夾
- `headers`：HTTP 請求標頭
- `avoid_urls`：略過檢查的網址
- `scan_urls`：起始掃描網址
- `url_normalization`：URL 正規化規則，控制快取與去重方式
- `download_link_rules`：下載型連結判定規則，控制哪些內部連結不再往下遞迴
- `soft_404_rules`：soft-404 關鍵字與判定門檻
- `redirect_rules`：redirect 類型與可疑導向判定規則
- `request_control`：重試次數、退避秒數與同網域最小請求間隔

以上欄位都屬於使用者端的掃描設定。更新伺服器位置不放在 `data\config.yaml` 中，而是由 [chklink_config.py](chklink_config.py) 內的常數統一管理，避免一般使用者誤改。

### 關於自訂 Header 與 Cookie

- 預設設定已不再內建 `Cookie` 或其它 session/token 類值，避免公開 repo 時把敏感請求資料一併帶出。
- 若某些站台必須依賴登入態、SSO 或特定 session 才能開啟，請由使用者自行在 `data\config.yaml` 的 `headers` 區塊補上需要的值。
- 這表示：公開網站的掃描通常不受影響；需要驗證狀態的頁面，則需自行提供對應 header。

若你是從 GitHub clone 本專案到自己的環境，通常應修改的是 [chklink_config.py](chklink_config.py) 內的：

- `DEFAULT_RELEASE_BASE_URL`
- `DEFAULT_REMOTE_VERSION_FILE`
- `DEFAULT_SETUP_FILE`

這樣就能把 GUI 更新按鈕改指向你自己的下載伺服器，而且不需要把部署端設定曝露在使用者的 `data\config.yaml` 中。

## 版本號來源

目前版本號與產品名稱的主要來源在 [chklink_config.py](chklink_config.py)：

- `APP_NAME`
- `APP_DISPLAY_NAME`
- `DEFAULT_APP_VERSION`

這三個常數會同時影響：

- GUI 視窗標題顯示的版本
- Inno Setup 安裝程式顯示名稱
- 桌面與開始功能表捷徑名稱
- `make_exec.cmd` 傳給 Nuitka 的：
  - `--product-name`
  - `--file-version`
  - `--product-version`

因此若要發新版，建議優先修改這三個常數，再重新編譯與部署。

### 版本規則

本專案採用 Semantic Versioning（SemVer）精神，但判斷依據不是 Python 函式庫 API，而是這個桌面工具對外的可依賴行為，例如：

- GUI 與 CLI 的使用方式
- `data\config.yaml` 的設定格式
- Excel 報表欄位與輸出格式
- 安裝、升級與更新流程
- `RemoteVersion.yaml` 與發佈檔名規則

建議版本遞增原則如下：

- `PATCH`：向下相容的修正，例如 bug fix、文件修正、打包修正
- `MINOR`：向下相容的新功能，例如新增掃描規則、報表欄位或發佈輔助工具
- `MAJOR`：不相容變更，例如設定格式大改、CLI 參數不相容、報表格式大改、更新機制重大變更

另外，已公開發佈的版本內容不應再原地修改；若發佈後有任何實質變更，應以新版本重新發佈。

## 編譯成執行檔

### 前置需求

- Windows
- Python 3.12
- 已安裝專案相依套件
- 可用的 `.venv` 或系統 Python
- 已安裝 Nuitka

### 安裝相依套件

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install nuitka
```

### 編譯步驟

執行：

```cmd
make_exec.cmd
```

`make_exec.cmd` 的定位是「第 1 階段：編譯與準備版本檔」，它會：

- 優先使用 `.venv\Scripts\python.exe`
- 檢查 `nuitka`、`chklink.py`、`chklink.ico` 是否存在
- 自動從 `chklink_config.py` 讀取 `APP_NAME` 與 `DEFAULT_APP_VERSION`
- 確保 `data\update.cmd` 存在
- 清除舊的 `out`、`build`
- 將 `icon\folder.png` 一起打包進 standalone 資料夾
- 將版本資訊帶入執行檔屬性
- 用 Nuitka 以 `--standalone` 將 `chklink.py` 打包成 GUI 程式資料夾
- 另外用 Nuitka 產出 `out\chklink_cli.exe`
- 另外同步產生 `installer\<版本>\RemoteVersion.yaml`
- 產出 `out\chklink.dist\chklink.exe`

目前正式建議的打包方式是 `standalone`，因為實測 `onefile` 容易在部分電腦被防毒或 Windows 安全機制攔截。

## 正式發佈與升級流程

目前正式建議的 Windows 發佈路線是：

1. 先用 `make_exec.cmd` 產生 GUI / CLI 編譯產物與 `RemoteVersion.yaml`
2. 若需要對 GUI / CLI 加簽，執行 `make_sign_app.cmd`
3. 再用 `make_setup.cmd` 透過 Inno Setup 封裝成對應版本的安裝程式
4. 若需要對 installer 加簽，執行 `make_sign_setup.cmd`
5. 對外提供 `installer\<版本>\chklink_setup.exe` 與 `installer\<版本>\RemoteVersion.yaml`

也就是說，目前正式發佈品不是單一 `chklink.exe`，而是：

- `out\chklink.dist\`：GUI 的 `standalone` 多檔案執行目錄
- `out\chklink_cli.exe`：CLI 執行檔
- `installer\<版本>\chklink_setup.exe`：對外提供的正式安裝程式
- `installer\<版本>\RemoteVersion.yaml`：提供 GUI 檢查更新時比對版本用的遠端版本檔

### 發佈前置需求

除了 Python / Nuitka 之外，若要完整走完正式發佈流程，還需要：

- Inno Setup 6
- `ChineseTraditional.isl` 繁體中文語系檔
- 視需要準備 `signtool.exe` 與可用的簽章憑證

Inno Setup 語系檔安裝方式如下：

1. 安裝 Inno Setup 6。
2. 到 Inno Setup 官方翻譯頁下載繁體中文語系：
   - [Inno Setup Translations](https://jrsoftware.org/files/istrans/)
3. 在頁面中找到 `Chinese (Traditional)`，下載 `ChineseTraditional.isl`。
4. 將 `ChineseTraditional.isl` 放到 Inno Setup 安裝目錄下的 `Languages` 資料夾，例如：
   - `C:\Program Files (x86)\Inno Setup 6\Languages\ChineseTraditional.isl`

`build_setup.ps1` 會先檢查 `ISCC.exe` 與 `ChineseTraditional.isl` 是否存在，任一缺少都會直接停止。

### 發佈產物的分工

`make_exec.cmd` 負責編出正式程式本體，會：

- 讀取 `chklink_config.py` 的 `APP_NAME` 與 `DEFAULT_APP_VERSION`
- 確保 `data\update.cmd` 存在
- 以 `standalone` 模式產生 `out\chklink.dist\chklink.exe`
- 另外產生 `out\chklink_cli.exe`
- 直接產生 `installer\<版本>\RemoteVersion.yaml`

這樣可以確保：

- 執行中的 GUI / CLI 版本
- 下載伺服器上的 `RemoteVersion.yaml`

三者一致。

`make_sign_app.cmd` 的定位是「第 2 階段：先簽 GUI / CLI」，它會呼叫 `sign_files.ps1 -Target app`。

`make_setup.cmd` 的定位是「第 3 階段：建立 installer」，它會直接轉呼叫 `build_setup.ps1`。

`build_setup.ps1` 則負責把編譯產物封裝成安裝程式，它會：

- 讀取 `chklink_config.py` 的 `APP_NAME`、`APP_DISPLAY_NAME`、`DEFAULT_APP_VERSION`
- 讀取 `installer_template.iss` 作為穩定模板
- 依版本、路徑與顯示名稱產生 `installer\build.iss`
- 將 `out\chklink.dist`、`out\chklink_cli.exe` 與 `data\update.cmd` 一起包進安裝檔
- 呼叫 Inno Setup 6 的 `ISCC.exe`
- 產出 `installer\<版本>\chklink_setup.exe`

`make_sign_setup.cmd` 的定位是「第 4 階段：最後再簽 installer」，它會呼叫 `sign_files.ps1 -Target setup`。

### 為什麼 installer 不再包含 `data\config.yaml`

正式路線改成 `standalone + Inno Setup` 後，安裝與升級都共用同一個 `setup.exe`。若 installer 內包含 `data\config.yaml`，使用者之後重新執行新版安裝程式覆蓋安裝時，就容易把：

- `data\config.yaml`
- `data\visited_link.yaml`

這些使用者自己的設定與快取一併洗掉。

因此目前採取的原則是：

- installer 內不包含 `data\config.yaml`
- installer 內不包含 `data\visited_link.yaml`
- GUI 第一次啟動時若找不到 `data\config.yaml`，才在本機建立預設設定檔
- `data\visited_link.yaml` 則維持掃描後才建立

這樣做有兩個好處：

1. 首次安裝與升級都走同一套 `setup.exe` 流程。
2. 重新安裝新版時，不會覆蓋使用者自己的設定與快取。

### 正式發佈 SOP

建議每次發版都照下面順序執行：

1. 先更新 [chklink_config.py](chklink_config.py) 的版本與必要顯示名稱。
2. 執行 `make_exec.cmd`，產生：
   - `out\chklink.dist\chklink.exe`
   - `out\chklink_cli.exe`
   - `installer\<版本>\RemoteVersion.yaml`
3. 若要先對 GUI / CLI 加簽，執行 `make_sign_app.cmd`。
4. 執行 `make_setup.cmd`，產生：
   - `installer\<版本>\chklink_setup.exe`
5. 若要對 installer 加簽，再執行 `make_sign_setup.cmd`，它會簽：
   - `installer\<版本>\chklink_setup.exe`
6. 若要提供雜湊驗證，再執行 `make_sha256.cmd`，產生：
   - `installer\<版本>\SHA256.txt`
7. 實際安裝一次，確認安裝介面、捷徑、主程式啟動與版本資訊都正確。
8. 先上傳 `chklink_setup.exe`，確認可下載後，再上傳 `RemoteVersion.yaml`。

也就是說，日常 build / 發版分工如下：

1. `make_exec.cmd`：編譯 GUI / CLI，並準備 `RemoteVersion.yaml`
2. `make_sign_app.cmd`：先對 GUI / CLI 加簽
3. `make_setup.cmd`：建立 installer
4. `make_sign_setup.cmd`：最後對 installer 加簽
5. `make_sha256.cmd`：可選，產生 `SHA256.txt`
6. `menu.cmd`：提供 `1 / 2 / 3 / 4 / 5 / 6` 的互動式選單入口
7. `make_github_release.cmd`：可選，整理 GitHub Release 檔案

### `menu.cmd` 選單與實際腳本的對應

- `menu.cmd` 只是手動選單入口，不是實際的編譯腳本。
- 選單 `1` 對應 `make_exec.cmd`
- 選單 `2` 對應 `make_sign_app.cmd`
- 選單 `3` 對應 `make_setup.cmd`
- 選單 `4` 對應 `make_sign_setup.cmd`
- 選單 `5` 對應 `make_sha256.cmd`
- 選單 `6` 對應 `make_github_release.cmd`
- 若要改建置流程，應優先改對應腳本本身，再同步確認 `menu.cmd` 是否仍一致。

### 上傳到下載伺服器的檔案

目前正式建議只需上傳：

- `installer\<版本>\chklink_setup.exe`
- `installer\<版本>\RemoteVersion.yaml`

若你也想讓使用者能驗證檔案完整性，建議另外附上：

- `installer\<版本>\SHA256.txt`

若要準備 GitHub Release 檔案，可再執行 `make_github_release.cmd`，它會建立：

- `release\<版本>\chklink-<version>-win-x64-setup.exe`
- `release\<版本>\chklink-<version>-RemoteVersion.yaml`
- `release\<版本>\chklink-<version>-SHA256.txt`

這個步驟只負責整理對外公開發佈檔名，不會改動 GUI 預設更新來源；GUI 預設仍建議指向組織內部發佈站。

### 組織內部更新與 GitHub Release 的分工

- 組織內部更新線：
  - 主要給 GUI「檢查更新」使用
  - 使用 `installer\<版本>\chklink_setup.exe`
  - 使用 `installer\<版本>\RemoteVersion.yaml`
- GitHub Release 線：
  - 主要給對外公開下載與版本展示使用
  - 使用 `release\<版本>\chklink-<version>-win-x64-setup.exe`
  - 使用 `release\<版本>\chklink-<version>-RemoteVersion.yaml`
  - 使用 `release\<版本>\chklink-<version>-SHA256.txt`
- 這兩條線目前共用同一套程式本體，但下載檔名與使用目的不同。

若你要部署到自己的伺服器，請同時確認：

- 下載伺服器上的檔名與 `DEFAULT_REMOTE_VERSION_FILE`、`DEFAULT_SETUP_FILE` 一致
- [chklink_config.py](chklink_config.py) 內的 `DEFAULT_RELEASE_BASE_URL` 已改成你的伺服器路徑

### GitHub Release 說明範本

若你要在 GitHub 建立 Release，可直接參考下面這份說明文字，再依當版內容調整：

```markdown
## chkLink 1.4.0

### 本版重點

- 掃描網站內部失效連結
- 列出頁面中的外部連結
- 檢查圖片是否缺少 alt
- 輸出 Excel 報表
- 補強 URL 正規化、下載判定、soft-404 / redirect 類型判斷
- 補強 retry、backoff 與每網域節流
- 提供 SHA256 與 GitHub Release 檔案整理流程

### 下載檔案

- `chklink-1.4.0-win-x64-setup.exe`：Windows x64 安裝版
- `chklink-1.4.0-RemoteVersion.yaml`：版本資訊
- `chklink-1.4.0-SHA256.txt`：雜湊驗證檔

### 注意事項

- 首次下載執行時，Windows SmartScreen 或 Smart App Control 仍可能出現提示。
- 若此版本已確認穩定，且仍遭 Microsoft 防護機制誤判，可再提交檔案到 https://www.microsoft.com/en-us/wdsi/filesubmission 回報。或關閉「智慧型應用程式控制」。
- GUI 預設更新來源仍建議使用組織內部發佈站；GitHub Release 主要提供對外公開下載。

### SHA256 驗證

請參考 `chklink-1.4.0-SHA256.txt`。
```

建議在每次正式發版時，把上面的版本號、重點摘要與檔名同步改成當次版本。

### 公開 Repo 前的注意事項

- 不要把真實的 `Cookie`、token、Authorization header、帳密、或其它登入態資料放進 `config.yaml-default`、`chklink_config.py` 或 README。
- `data\config.yaml` 與 `data\visited_link.yaml` 屬於執行期檔案，不應提交。
- `sign_files.ps1` 內目前的憑證 thumbprint 不等於私鑰，但若未來改成更敏感的簽章設定，建議改放本機私有設定，不要直接提交。
- 若要公開 repo，建議先自行搜尋一次關鍵字：`Cookie`、`Authorization`、`token`、`password`、`thumbprint`，確認沒有誤放敏感內容。

### 首次安裝流程

使用者端首次安裝流程如下：

1. 下載 `chklink_setup.exe`
2. 執行安裝程式
3. 安裝完成後，程式主體與 `data\update.cmd` 會先放好
4. 第一次啟動 GUI 時：
   - 若沒有 `data\config.yaml`，程式會在本機建立預設設定檔
   - 若沒有 `data\visited_link.yaml`，先不建立，等實際掃描完成後再建立

### 測試機安裝排除方式

若 `chklink_setup.exe` 在測試機上被 Windows 的智慧型應用程式控制或 SmartScreen 攔截，可先用下列方式排除；這些做法適合開發、測試或內部受控環境，不建議作為一般使用者的正式安裝指引。

1. 解除個別安裝檔的封鎖
   - 在 `chklink_setup.exe` 上按滑鼠右鍵，選擇「內容」。
   - 在視窗下方的「安全性」區域，若有看到「解除封鎖」，請勾選後按「確定」。

2. 關閉「智慧型應用程式控制」
   - 路徑：
     - [開始] > [設定] > [隱私權與安全性] > [Windows 安全性] > [應用程式和瀏覽器控制]
   - 點擊「智慧型應用程式控制設定」，切換為「關閉」。

補充：

- 這兩種方式主要是為了測試機排除阻擋，不是正式對外散布的根本解法。
- 若要降低一般使用者被攔截的機率，仍建議維持穩定簽章、固定下載來源，並盡量累積檔案聲譽。

若最後版本已確認穩定，且仍持續被智慧型應用程式控制（Smart App Control）或 Microsoft 相關防護機制誤判，也可以再向 Microsoft 提交檔案回報：

- 檔案提交入口：
  - https://www.microsoft.com/en-us/wdsi/filesubmission
- 提交時建議附上的說明重點：
  - 這是網站失效連結掃描工具
  - 主要用途是檢查網站內部連結是否失效、列出外部連結、檢查圖片 `alt`、並輸出報表
  - 發佈形式為 `chklink_setup.exe` 安裝程式
  - 若已完成簽章，也可一併說明簽章狀態與下載來源

這個做法比較適合在版本內容已確認、不會再頻繁重包之後進行；若檔案雜湊一直改變，回報效果通常會比較有限。

### 升級流程

目前正式建議的升級方式是：

1. GUI 按「檢查更新」
2. 下載遠端 `RemoteVersion.yaml`
3. 和程式內建的 `DEFAULT_APP_VERSION` 比對版本
4. 若遠端較新：
   - 下載同一台伺服器上的 `chklink_setup.exe`
   - 交給 `data\update.cmd` 啟動新版安裝程式
5. 使用者依原路徑覆蓋安裝
6. 升級完成後：
   - 程式檔更新
   - `data\config.yaml` 保留
   - `data\visited_link.yaml` 保留

### GUI 內的「檢查更新」按鈕實際流程

目前 GUI 的「檢查更新」按鈕已直接走新版 installer 升級邏輯，實際步驟如下：

1. 先讀取程式內建的 `DEFAULT_APP_VERSION` 作為本機版本。
2. 再依 [chklink_config.py](chklink_config.py) 中的發佈常數組合更新網址：
   - `DEFAULT_RELEASE_BASE_URL`
   - `DEFAULT_REMOTE_VERSION_FILE`
   - `DEFAULT_SETUP_FILE`
3. 程式會用 `DEFAULT_RELEASE_BASE_URL + 檔名` 組合出實際下載網址。
4. 下載遠端 `RemoteVersion.yaml` 到暫存目錄。
5. 比對遠端版本與本機版本。
6. 若遠端較新，詢問是否下載並啟動新版安裝程式。
7. 使用者同意後：
   - 下載 `chklink_setup.exe` 到系統暫存目錄
   - 呼叫 `data\update.cmd`
8. `data\update.cmd` 會：
   - 關閉目前執行中的 `chklink.exe`
   - 啟動剛下載好的 `chklink_setup.exe`
9. 之後由 Inno Setup 覆蓋安裝新版程式。

### `data\update.cmd` 的角色

目前 `data\update.cmd` 不再負責舊版那種單一 `exe` 替換，而是改成：

- 關閉目前執行中的 `chklink.exe`
- 啟動已下載好的新版 `chklink_setup.exe`

這樣做的原因是，正式發佈型態已經改成：

- `standalone` 多檔案結構
- 再由 Inno Setup 封裝為 `setup.exe`

在這個前提下，真正要更新的已不只是 `chklink.exe`，還包含整個程式目錄中的 DLL、模組、資源檔與安裝資訊，因此由 installer 覆蓋安裝會比自行替換單一 `exe` 更穩定。

### GUI 與 CLI 的發佈定位

- 目前正式發佈流程會同時產生 GUI 與 CLI 兩個執行檔。
- installer 會一併安裝 GUI 與 CLI，但只為 GUI 建立桌面與開始功能表捷徑。
- GUI 是主要對外入口；CLI 採低曝光設計，保留給排程、自動化與除錯用途。

## 為什麼需要 `sign_files.ps1`

部分電腦或防毒產品會把新編譯出的執行檔或 installer 視為可疑檔案，甚至直接隔離或刪除。`sign_files.ps1` 是用來降低這類問題的簽章腳本，目前支援：

- `-Target app`：處理 `out\chklink.dist\chklink.exe` 與 `out\chklink_cli.exe`
- `-Target setup`：處理 `installer\<版本>\chklink_setup.exe`
- `-Target all`：一次處理上述全部檔案

它做的事情是：

- 使用 `signtool.exe` 對 GUI、CLI 或 installer 做 Authenticode 簽章
- 用既有憑證指紋 `/sha1 ...` 指定簽章憑證
- 透過 Sectigo 時間戳服務加上時間戳

### 這代表什麼

- 我懂，這支腳本是在處理「執行檔信任度」問題，不是掃描邏輯的一部分。
- 它無法保證所有防毒都不誤判，但通常能降低 SmartScreen、端點防護或防毒軟體把新編譯執行檔視為未知程式的機率。
- 若沒有可用憑證或 `signtool.exe`，即使編譯成功，也可能在某些電腦上被攔截或刪除。
- `SignTool` 不建議直接隨本專案一起發佈；較適合在說明文件中提示安裝 Windows SDK 或既有簽章工具路徑，再由使用者自行準備環境。

### 自然人憑證與加簽的補充說明

這段很重要，建議後續維護時直接先看這裡。

- MOICA 官方說明，自然人憑證的主要用途是「身分識別」、「數位簽章」與「加解密」，私鑰存放在實體 IC 卡或行動裝置安全區，不能任意匯出。
- Microsoft `SignTool` 在簽檔時，預設要求簽章憑證具備 `Code Signing` EKU，OID 為 `1.3.6.1.5.5.7.3.3`。
- 因此，「自然人憑證可以做數位簽章」不等於「自然人憑證一定能直接拿來做 Windows 執行檔 Authenticode 簽章」。

實務上若要用自然人憑證嘗試加簽，至少要同時滿足下列條件：

1. 電腦已安裝自然人憑證讀卡機與對應中介軟體。
2. 卡片已插入，且目前登入帳號有權限使用該私鑰。
3. 該張卡在 Windows 憑證存放區中可被 `signtool.exe` 看見。
4. 該憑證實際延伸金鑰用法或金鑰提供者可滿足 Authenticode 簽章需求。
5. `sign_files.ps1` 中指定的 SHA-1 thumbprint 必須對應到目前可用的那張憑證。

若其中任一項不成立，就算你手上有自然人憑證，也可能無法完成加簽。

### 如何判斷應該用哪張自然人憑證

自然人憑證卡上通常不只一張憑證，至少常見會有：

- 簽章憑證：用途通常為「數位簽章」
- 加密憑證：用途通常為「金鑰加密」或「資料加密」

若要搭配 `SignTool` 對 `chklink.exe` 做簽章，應優先使用「簽章憑證」，不要誤用加密憑證。

放進 Windows 憑證存放區與 `SignTool` 工具使用的，必須是簽章憑證的雜湊值（thumbprint），不要誤用加密憑證；實際使用值仍應以當下電腦與卡片環境重新確認，不要只沿用舊機器留下的設定。

最直接的查法是先執行：

```powershell
certutil -scinfo
```

執行時通常會稍等幾秒後跳出 PIN 碼輸入視窗；完成驗證後，才會繼續列出智慧卡上的憑證資訊。

這份輸出很長，重點只看「簽章憑證資訊」那一段：

- `簽章憑證資訊`
- 金鑰用途是否為「數位簽章」
- `Cert 雜湊(sha1)`

其中：

- `Cert 雜湊(sha1)` 就是之後要填進 `sign_files.ps1` 的 `$thumbprint`

若覺得 `certutil -scinfo` 輸出太長，不好直接找，可用下面這條指令直接抓出第一張簽章憑證的 `Cert 雜湊(sha1)`：

```powershell
(certutil -scinfo | Select-String 'Cert 雜湊\(sha1\)' | Select-Object -First 1).ToString().Split(':')[-1].Trim()
```

正常情況下會直接輸出可填入 `sign_files.ps1` 的值，例如：

```text
63dc665f1795f66146cf1096d956fd797060af24
```

接著再填回 `sign_files.ps1`：

```powershell
$thumbprint = '63dc665f1795f66146cf1096d956fd797060af24'
```

`sign_files.ps1` 的 `$fileDigestAlgorithm` 仍應以 `SignTool` 實測可成功的結果為準，不能只因為憑證本身顯示 `sha256RSA`，就直接假設 `/fd SHA256` 一定可用。

### 對這個專案的實際意義

- [sign_files.ps1](sign_files.ps1) 目前是以 `/sha1 63dc665f1795f66146cf1096d956fd797060af24` 指定 Windows 憑證存放區中的簽章憑證。
- 這表示它依賴的是「當時那台電腦上可被 `SignTool` 使用的憑證」，不是單靠檔案就能完成。
- 若未來更換電腦、換卡、重發憑證、更新卡片中介軟體，或憑證指紋改變，就必須同步更新 `sign_files.ps1`。
- 若未來發現自然人憑證在某台機器上能做文件簽章，但 `signtool.exe` 仍無法對這三個發佈檔案加簽，優先懷疑的是：
  - 憑證沒有符合 `Code Signing` 用途
  - 憑證雖存在，但 `SignTool` 無法透過 CSP / KSP 存取私鑰
  - 指定的 thumbprint 已不是目前有效憑證

### 官方參考資料

- MOICA 自然人憑證用途說明：
  - https://moica.nat.gov.tw/other/what.html
  - https://moica.nat.gov.tw/en/what.html
- Microsoft SignTool 與程式碼簽章憑證需求：
  - https://learn.microsoft.com/zh-tw/windows/win32/seccrypto/signtool
  - https://learn.microsoft.com/en-us/windows/win32/appxpkg/how-to-sign-a-package-using-signtool

### SignTool 準備建議

- 若電腦尚未安裝 `signtool.exe`，建議透過 Windows SDK 取得，不需把 `SignTool` 整包放進本專案。
- 實際安裝後，`signtool.exe` 常見位置會落在 Windows SDK 的 `bin` 目錄下；若與 [sign_files.ps1](sign_files.ps1) 目前寫死的路徑不同，請依實際環境調整腳本。
- 若未來要在其他電腦交接簽章流程，建議 README 保留下載來源、安裝方式與 `sign_files.ps1` 修改位置說明即可。

### 建議流程

1. 先跑 `make_exec.cmd`
2. 若要先對 GUI / CLI 加簽，再跑 `make_sign_app.cmd`
3. 再跑 `make_setup.cmd`
4. 若要對 installer 加簽，再跑 `make_sign_setup.cmd`
5. 先提供新的安裝程式，最後再更新 `RemoteVersion.yaml`

## 已知限制

- GUI 與 CLI 目前都依賴 Selenium Manager 取得可用的 ChromeDriver。
- 若 Chrome 未安裝，或 Selenium Manager 在該環境無法正常取得 driver，Selenium 備援會失敗。
- GUI 與 CLI 目前已共用主要掃描核心，但入口、介面與操作流程仍分開維護，修改時仍要一起確認。
- 若未來仍要恢復程式內自動更新，需重新設計 `standalone` 安裝版的升級方式，不宜直接沿用舊的單一執行檔替換流程。

## 編碼與換行

- `.py`、`.md`：UTF-8 無 BOM
- `.cmd`：Big5 / cp950
- `.ps1`、`.yaml`：UTF-8 無 BOM
- 文字檔換行：CRLF

## 維護提醒

- 處理 UTF-8 檔案時，不要使用 PowerShell 文字管線，以免繁體中文毀損。
- 若調整安裝流程，請同步檢查 `make_exec.cmd`、`menu.cmd`、`build_setup.ps1`、`installer_template.iss` 與 `sign_files.ps1` 是否仍相容。
- 若未來要再調整程式內更新流程，請先確認 GUI 文案、`run_update()`、`make_exec.cmd`、`menu.cmd`、`make_sign_app.cmd`、`make_setup.cmd`、`make_sign_setup.cmd` 與 `data\update.cmd` 是否整體一致。
- 若修改 GitHub Release 相關流程，請同步確認 `make_github_release.cmd`、README 的 Release 範本與實際輸出檔名是否一致。
