# chkLink

`chkLink` 是一套用來掃描網站失效連結的 Windows 工具，提供 GUI 與 CLI 兩種使用方式。它會遞迴掃描站內頁面、驗證內部連結、列出外部連結、檢查圖片是否缺少 `alt`，並輸出 Excel 報告與 log 紀錄，方便網站維護人員定期盤點問題。

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
- `chklinkTerminal.py`：CLI 主程式
- `config.yaml`：實際使用的設定檔
- `config.yaml-default`：預設設定樣板
- `visited_link.yaml`：已檢查過且回應正常的連結快取
- `LocalVersion.yaml`：本機版本資訊
- `run.cmd`：啟動 GUI
- `make.cmd`：編譯 GUI 執行檔
- `make_setup.ps1`：產生 Inno Setup 安裝程式
- `chklink_setup.iss`：Inno Setup 安裝腳本
- `make1.cmd`：包裝腳本，會轉呼叫 `make_setup.ps1`
- `update.cmd`：初始化資源與舊版替換式更新使用的批次檔
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

GUI 啟動時會：

- 若缺少 `config.yaml`，會先嘗試下載 `resources.7z` 補齊初始化檔案
- 若下載失敗，才退回本機建立預設檔案
- 讀取 `config.yaml`
- 若存在則載入 `visited_link.yaml`；此檔為成功連結快取，通常會在完成一次掃描並儲存結果後建立或更新

若是透過 Inno Setup 安裝，安裝程式本身就會先放好 `config.yaml`、`LocalVersion.yaml` 與 `update.cmd`，因此正常情況下不會在第一次啟動時觸發 `resources.7z` 初始化下載。

CLI 版 `chklinkTerminal.py` 不參與初始化資源下載與安裝程式更新流程；若缺少 `config.yaml` 或 `LocalVersion.yaml`，仍會依既有邏輯在本機建立 fallback 檔案。

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
- 檢查 7-Zip 是否可用
- 檢查 `config.yaml-default`、`LocalVersion.yaml`、`update.cmd` 是否存在
- 自動從 `chklink_config.py` 讀取 `APP_NAME` 與 `DEFAULT_APP_VERSION`
- 先依 `DEFAULT_APP_VERSION` 重寫 `LocalVersion.yaml`
- 清除舊的 `out`、`build`
- 將 `icon\folder.png` 一起打包進 standalone 資料夾
- 將版本資訊帶入執行檔屬性
- 用 Nuitka 以 `--standalone` 將 `chklink.py` 打包成 GUI 程式資料夾
- 另外產生 `resources.7z`
  - 內容包含 `config.yaml-default` 改名後的 `config.yaml`、`LocalVersion.yaml`、`update.cmd`
- 產出 `out\chklink.dist\chklink.exe`

目前正式建議的打包方式是 `standalone`，因為實測 `onefile` 容易在部分電腦被防毒或 Windows 安全機制攔截。

## 產生安裝檔

### 安裝 Inno Setup 與繁體中文語系

1. 先安裝 Inno Setup 6。
2. 到 Inno Setup 官方翻譯頁下載繁體中文語系：
   - [Inno Setup Translations](https://jrsoftware.org/files/istrans/)
3. 在頁面中找到 `Chinese (Traditional)`，下載 `ChineseTraditional.isl`。
4. 將 `ChineseTraditional.isl` 放到 Inno Setup 安裝目錄下的 `Languages` 資料夾，例如：
   - `C:\Program Files (x86)\Inno Setup 6\Languages\ChineseTraditional.isl`

`make_setup.ps1` 目前會先檢查這個語系檔是否存在；若不存在，會直接提示錯誤並停止。

執行：

```powershell
.\make_setup.ps1
```

`make_setup.ps1` 會：

- 讀取 `chklink_config.py` 的 `APP_NAME` 與 `DEFAULT_APP_VERSION`
- 自動重寫 `chklink_setup.iss` 內的版本與路徑設定
- 呼叫 Inno Setup 6 的 `ISCC.exe`
- 將 `out\chklink.dist` 與必要初始化檔一起打包成安裝程式
- 使用 `ChineseTraditional.isl` 產生繁體中文安裝介面
- 產出 `installer\chklink_setup.exe`

因此若版本從 `1.4` 改成 `1.5`，只要先更新 `chklink_config.py`，再重新執行 `make_setup.ps1`，安裝檔版本資訊就會同步更新。

## 初始化資源與安裝方式

目前正式發佈路線已改為：

- `make.cmd`：產生 `standalone` 執行資料夾與 `deploy\resources.7z`
- `make_setup.ps1`：再將 `standalone` 資料夾封裝成 `installer\chklink_setup.exe`

這樣設計的原因是：過往實測發現，若 `chklink.exe` 一啟動就立刻在本機自動建立初始化檔案，或採用 `onefile` 自解壓模式，較容易被防毒或 Windows 安全機制視為可疑行為。因此目前改成：

- 正式安裝版由 Inno Setup 先把必要檔案安裝到程式目錄
- 直接執行原始碼或未經安裝版時，才在 `config.yaml` 缺少時優先下載 `resources.7z`
- 只有下載失敗時，才退回本機自動建立 `config.yaml`

`resources.7z` 由 `make.cmd` 產生，內容為：

- `config.yaml`
- `LocalVersion.yaml`
- `update.cmd`

其中 `config.yaml` 的來源是 `config.yaml-default`，只是打包時改名，方便首次初始化直接使用。

## 升級方式

目前 GUI 裡的「升級說明」按鈕只會提示使用者改用新版安裝程式，不再提供程式內自動下載與替換執行檔的更新流程。

原因是目前正式發佈方式已改為：

- `standalone` 多檔案結構
- 再由 Inno Setup 封裝為 `setup.exe`

這代表真正要更新的已不只是單一 `chklink.exe`，而是整個程式目錄中的多個檔案。若仍沿用舊的：

- `update.7z`
- `RemoteVersion.yaml`

只替換單一 `exe` 的方式，容易出現下列問題：

- `standalone` 目錄內其他 DLL、模組或資料檔沒有同步更新
- 安裝位置若在 `Program Files`，程式內自動覆蓋檔案常需要額外權限
- Inno Setup 安裝版建立的捷徑、解除安裝資訊與安裝紀錄也不會同步更新

正式建議做法是：

1. 重新執行 `make.cmd`
2. 視需要執行 `pycert.ps1` 對 `out\chklink.dist\chklink.exe` 簽章
3. 再執行 `make_setup.ps1`
4. 將新的 `installer\chklink_setup.exe` 提供給使用者重新安裝或覆蓋安裝

若習慣沿用舊入口，也可以直接執行：

```cmd
make1.cmd
```

目前 `make1.cmd` 已改為包裝腳本，會先詢問是否執行 `pycert.ps1` 進行簽章，之後再轉呼叫 `powershell -ExecutionPolicy Bypass -File ".\make_setup.ps1"`，方便從既有批次流程延續使用。

### 是否還能沿用 `update.7z` 與 `RemoteVersion.yaml`

可以，但前提是你願意另外重做一套專屬於 `standalone` 的更新流程，而不能直接沿用目前舊的單一執行檔替換邏輯。

若未來真的想保留「程式內更新」功能，至少要同時處理：

- 更新包改為包含整個 `standalone` 需要更新的檔案，而不只是 `chklink.exe`
- `update.cmd` 要能在關閉程式後批次替換多個檔案
- 需要排除或保留使用者資料，例如：
  - `config.yaml`
  - `visited_link.yaml`
- 若安裝目錄在 `Program Files`，可能還要額外處理權限或改採每使用者安裝路徑

所以結論是：

- 技術上不是完全不能做
- 但那會是一套新的 `standalone` 更新設計
- 在目前這個版本，重新提供新版 `setup.exe` 讓使用者覆蓋安裝，仍是最單純也最穩定的方式

### GUI 與 CLI 的發佈定位

- 目前正式發佈、打包、簽章與安裝流程，都是以 GUI 版 `chklink.py` / `chklink.exe` 為主。
- CLI 版 `chklinkTerminal.py` 不參與 Inno Setup 安裝流程與 GUI 升級提示，目前仍以原始碼執行為主。
- 若未來要發佈 CLI 執行檔，建議另外規劃 CLI 專用的安裝與更新方式，避免與 GUI 發佈產物混用。

## 為什麼需要 `pycert.ps1`

部分電腦或防毒產品會把新編譯出的 `chklink.exe` 視為可疑檔案，甚至直接隔離或刪除。`pycert.ps1` 是用來降低這類問題的簽章腳本，目前會自動優先尋找：

- `out\chklink.dist\chklink.exe`
- `out\chklink.exe`

它做的事情是：

- 使用 `signtool.exe` 對找到的 `chklink.exe` 做 Authenticode 簽章
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

- `Cert 雜湊(sha1)` 就是之後要填進 `pycert.ps1` 的 `$thumbprint`

若覺得 `certutil -scinfo` 輸出太長，不好直接找，可用下面這條指令直接抓出第一張簽章憑證的 `Cert 雜湊(sha1)`：

```powershell
(certutil -scinfo | Select-String 'Cert 雜湊\(sha1\)' | Select-Object -First 1).ToString().Split(':')[-1].Trim()
```

正常情況下會直接輸出可填入 `pycert.ps1` 的值，例如：

```text
63dc665f1795f66146cf1096d956fd797060af24
```

接著再填回 `pycert.ps1`：

```powershell
$thumbprint = '63dc665f1795f66146cf1096d956fd797060af24'
```

`pycert.ps1` 的 `$fileDigestAlgorithm` 仍應以 `SignTool` 實測可成功的結果為準，不能只因為憑證本身顯示 `sha256RSA`，就直接假設 `/fd SHA256` 一定可用。

### 對這個專案的實際意義

- [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1) 目前是以 `/sha1 63dc665f1795f66146cf1096d956fd797060af24` 指定 Windows 憑證存放區中的簽章憑證。
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
2. 視需要執行 `pycert.ps1` 對 `out\chklink.dist\chklink.exe` 簽章
3. 再跑 `make_setup.ps1` 產生 `installer\chklink_setup.exe`
4. 將新的安裝程式提供給使用者安裝或覆蓋安裝

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

- 還原 UTF-8 檔案時，不要使用 PowerShell 文字管線，以免繁體中文再度毀損。
- 若調整安裝流程，請同步檢查 `make.cmd`、`make_setup.ps1`、`chklink_setup.iss` 與 `pycert.ps1` 是否仍相容。
- 若未來要重新啟用程式內更新，請先確認 GUI 文案、`run_update()`、`make1.cmd` 與 `update.cmd` 是否整體一致。
