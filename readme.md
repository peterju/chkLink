# chkLink

`chkLink` 是一套用來掃描網站失效連結的 Windows 工具，提供 GUI 與 CLI 兩種使用方式。它會遞迴掃描站內頁面、驗證內部連結、列出外部連結、檢查圖片是否缺少 `alt`，並輸出 Excel 報告與 log 紀錄，方便網站維護人員定期盤點問題。

## 專案用途

- 掃描網站中的內部連結是否可正常開啟
- 列出頁面上的外部連結，不對外站發送連通性驗證請求
- 額外標示不安全的 `http://` 連結
- 檢查圖片是否缺少 `alt` 屬性
- 產生 `.xlsx` 報告與 `.log` 紀錄
- 支援版本檢查與執行檔自我更新

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
- `chklinkTerminal.py`：CLI 主程式
- `config.yaml`：實際使用的設定檔
- `config.yaml-default`：預設設定樣板
- `visited_link.yaml`：已檢查過且回應正常的連結快取
- `LocalVersion.yaml`：本機版本資訊
- `run.cmd`：啟動 GUI
- `make.cmd`：編譯 GUI 執行檔
- `make1.cmd`：產生部署更新檔
- `update.cmd`：更新時替換執行檔
- `pycert.ps1`：對產生的執行檔做程式簽章

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
python chklinkTerminal.py
```

## GUI 重要邏輯

### 1. 啟動與初始化

GUI 與 CLI 啟動時都會：

- 建立 `update.cmd`，若檔案不存在就自動補齊
- 讀取 `config.yaml`
- 若首次執行缺少 `config.yaml` 或 `LocalVersion.yaml`，會在本機自動建立預設檔案
- 若存在則載入 `visited_link.yaml`；此檔為成功連結快取，通常會在完成一次掃描並儲存結果後建立或更新

其中只有 GUI 版會進一步建立視窗、分頁與設定控制項。

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
   - 若出現「連線逾時」或「無法連線至此網頁」，會再用 Selenium 實際打開頁面補驗
   - 若 `requests` 回應 `200`，但 HTML 明顯只是 Vue.js、React、Next.js、Nuxt 這類前端框架的初始殼頁，也會改用 Selenium 補驗
   - 若原始網址與實際落點網域不同，會標示為重定向
   - 若回應 `200` 但內容長度為 0，會標示為「內容為空」
6. 外部連結只會被列出，不會進行有效性驗證，也不會往下遞迴；但若外部連結使用 `http://`，仍會列成提醒。
7. 將錯誤連結、缺少 `alt` 的圖片、以及 `http://` 連結整理成記錄。
8. 掃描完成後呼叫共用核心輸出 Excel 報告，並把成功的連結存回 `visited_link.yaml`。

### 3. 已檢查連結快取

- GUI 上有「跳過已檢查過的網址」選項，CLI 也會讀取同一個 `skip_visited` 設定。
- 若啟用，程式會優先查 `visited_link.yaml`，避免對相同成功連結重複發送請求。
- 只有包含 `200` 的狀態會被寫回快取。
- `visited_link.yaml` 不一定會在首次啟動時出現；通常是在實際掃描完成並寫回快取後才建立。

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

`config.yaml` 主要欄位如下：

- `layer`：掃描深度
- `timeout`：逾時秒數
- `alt_must`：是否檢查圖片 `alt`
- `check_http`：是否標示 `http://` 連結
- `skip_visited`：是否略過已成功檢查過的網址
- `rpt_folder`：報告輸出資料夾
- `headers`：HTTP 請求標頭
- `avoid_urls`：略過檢查的網址
- `scan_urls`：起始掃描網址

## 版本號來源

目前版本號與產品名稱的主要來源在 [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)：

- `APP_NAME`
- `DEFAULT_APP_VERSION`

這兩個常數會同時影響：

- 首次執行時自動建立的 `LocalVersion.yaml`
- GUI 視窗標題顯示的預設版本
- `make.cmd` 傳給 Nuitka 的：
  - `--product-name`
  - `--file-version`
  - `--product-version`

因此若要發新版，建議優先修改這兩個常數，再重新編譯與部署。

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
make.cmd
```

`make.cmd` 會：

- 優先使用 `.venv\Scripts\python.exe`
- 檢查 `nuitka`、`chklink.py`、`chklink.ico` 是否存在
- 自動從 `chklink_config.py` 讀取 `APP_NAME` 與 `DEFAULT_APP_VERSION`
- 先依 `DEFAULT_APP_VERSION` 重寫 `LocalVersion.yaml`
- 清除舊的 `out`、`build`
- 將 `icon\folder.png` 一起打包進單檔執行檔
- 將版本資訊帶入執行檔屬性
- 用 Nuitka 以 `--onefile --standalone` 將 `chklink.py` 打包成單檔 GUI 程式
- 產出 `out\chklink.exe`

## 產生更新部署檔

執行：

```cmd
make1.cmd
```

`make1.cmd` 會：

1. 檢查 `out\chklink.exe` 是否已存在
2. 檢查 7-Zip 是否安裝於 `%ProgramFiles%\7-Zip\7z.exe`
3. 複製 `out\chklink.exe` 為 `chklink_upd.exe`
4. 打包 `update.7z`
   - 內容包含 `chklink_upd.exe`
5. 複製 `LocalVersion.yaml` 成 `deploy\RemoteVersion.yaml`
6. 將以上更新檔放到 `deploy\`

完成後主要部署產物為：

- `deploy\update.7z`
- `deploy\RemoteVersion.yaml`

## 其他電腦如何更新

GUI 裡的「檢查更新」按鈕會呼叫 `run_update()`，更新流程如下：

1. 先下載遠端的 `RemoteVersion.yaml`
2. 與本機 `LocalVersion.yaml` 比對版本號
3. 若遠端版本較新，下載 `update.7z`
4. 解壓出 `chklink_upd.exe`
5. 用 `update.cmd` 執行替換：
   - 關閉現有 `chklink.exe`
   - 將舊版改名為 `chklink.exe.old`
   - 將 `chklink_upd.exe` 改名為 `chklink.exe`
   - 啟動新版本

### 更新方式的本質

這套更新不是差分更新，也不是安裝包更新，而是：

- 由程式自行下載壓縮檔
- 解壓出新的單一執行檔
- 以批次檔方式做「檔案替換式更新」

所以要讓其他電腦能更新，必須把下列檔案放到程式預期下載的位置：

- `RemoteVersion.yaml`
- `update.7z`

目前首次啟動已不再依賴 `resources.7z`，因為：

- `folder.png` 會隨執行檔一起打包
- `LocalVersion.yaml` 若不存在，程式會在本機自動建立
- `config.yaml` 若不存在，也會在本機自動建立預設檔案

### GUI 與 CLI 的更新定位

- 目前正式發佈、打包與自動更新流程，都是以 GUI 版 `chklink.py` / `chklink.exe` 為主。
- CLI 版 `chklinkTerminal.py` 會共用建立 `update.cmd`、`config.yaml`、`LocalVersion.yaml` 等初始化流程，但目前不提供獨立的打包與自動更新機制。
- 若未來要發佈 CLI 執行檔，建議另外規劃 `make_cli.cmd` 與 CLI 專用的版本更新流程，避免和 GUI 發佈產物混用。

## 為什麼需要 `pycert.ps1`

部分電腦或防毒產品會把新編譯出的 `out\chklink.exe` 視為可疑檔案，甚至直接隔離或刪除。`pycert.ps1` 是先前用來降低這類問題的簽章腳本。

內容如下：

```powershell
..\SignTool\x64\signtool.exe sign /sha1 089a46b557607ae3bf629b07906b8931088107f3 /fd SHA1 /t http://timestamp.sectigo.com /v out\chklink.exe
```

它做的事情是：

- 使用 `signtool.exe` 對 `out\chklink.exe` 做 Authenticode 簽章
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
5. `pycert.ps1` 中指定的 SHA-1 thumbprint 必須對應到目前可用的那張憑證。

若其中任一項不成立，就算你手上有自然人憑證，也可能無法完成加簽。

### 對這個專案的實際意義

- [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1) 目前是以 `/sha1 089a46b557607ae3bf629b07906b8931088107f3` 指定 Windows 憑證存放區中的某一張憑證。
- 這表示它依賴的是「當時那台電腦上可被 `SignTool` 使用的憑證」，不是單靠檔案就能完成。
- 若未來更換電腦、換卡、重發憑證、更新卡片中介軟體，或憑證指紋改變，就必須同步更新 `pycert.ps1`。
- 若未來發現自然人憑證在某台機器上能做文件簽章，但 `signtool.exe` 仍無法對 `chklink.exe` 加簽，優先懷疑的是：
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
- 實際安裝後，`signtool.exe` 常見位置會落在 Windows SDK 的 `bin` 目錄下；若與 [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1) 目前寫死的路徑不同，請依實際環境調整腳本。
- 若未來要在其他電腦交接簽章流程，建議 README 保留下載來源、安裝方式與 `pycert.ps1` 修改位置說明即可。

### 建議流程

1. 先跑 `make.cmd`
2. 視需要執行 `pycert.ps1` 對 `out\chklink.exe` 簽章
3. 再跑 `make1.cmd` 產生更新部署檔
4. 將 `deploy\` 內容上傳到更新伺服器

## 已知限制

- GUI 與 CLI 目前都依賴 Selenium Manager 取得可用的 ChromeDriver。
- 若 Chrome 未安裝，或 Selenium Manager 在該環境無法正常取得 driver，Selenium 備援會失敗。
- GUI 與 CLI 目前已共用主要掃描核心，但入口、介面與操作流程仍分開維護，修改時仍要一起確認。
- `update.cmd` 為檔案替換式更新，若程式被防毒攔截，更新也可能失敗。

## 編碼與換行

- `.py`、`.md`：UTF-8 無 BOM
- `.cmd`：Big5 / cp950
- `.ps1`、`.yaml`：UTF-8 無 BOM
- 文字檔換行：CRLF

## 維護提醒

- 還原 UTF-8 檔案時，不要使用 PowerShell 文字管線，以免繁體中文再度毀損。
- 若調整更新流程，請同步檢查 `run_update()`、`make1.cmd`、`update.cmd`、`LocalVersion.yaml` 與遠端部署檔。
- 若調整編譯流程，請同步確認 `make.cmd` 與 `pycert.ps1` 是否仍相容。
