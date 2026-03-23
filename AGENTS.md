# AGENTS.md

## Project overview / 專案概要

- This is a Windows website link-checking project with two entry points.
- 這是一個 Windows 網站失效連結掃描專案，提供兩個入口。
- GUI: [chklink.py](/D:/pyTest/chkLink/chklink.py)
- CLI: [chklink_cli.py](/D:/pyTest/chkLink/chklink_cli.py)
- The main product is the GUI. The CLI is intentionally low-profile and is mainly for automation, scheduling, and debugging.
- 主要產品是 GUI；CLI 採低曝光設計，主要提供自動化、排程與除錯用途。
- The scan core is shared by both entry points and lives in [chklink_core.py](/D:/pyTest/chkLink/chklink_core.py).
- GUI 與 CLI 共用同一套掃描核心，位於 [chklink_core.py](/D:/pyTest/chkLink/chklink_core.py)。
- Runtime constants, versioning, config defaults, update URLs, and migration helpers live in [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py).
- 執行期常數、版本號、預設設定、更新網址與遷移輔助都集中在 [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)。

## Build and release commands / 建置與發佈指令

- Stage 1 build: `make.cmd`
- 第 1 階段：`make.cmd`
- Purpose: compile GUI and CLI, update `data\LocalVersion.yaml`, and write `installer\<version>\RemoteVersion.yaml`
- 作用：編譯 GUI 與 CLI，更新 `data\LocalVersion.yaml`，並產生 `installer\<版本>\RemoteVersion.yaml`
- GUI output: `out\chklink.dist\chklink.exe`
- GUI 輸出：`out\chklink.dist\chklink.exe`
- CLI output: `out\chklink_cli.exe`
- CLI 輸出：`out\chklink_cli.exe`

- Stage 2 setup packaging: `make_setup.cmd`
- 第 2 階段：`make_setup.cmd`
- Purpose: build `installer\<version>\chklink_setup.exe` through [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1) and [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss)
- 作用：透過 [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1) 與 [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss) 產生 `installer\<版本>\chklink_setup.exe`
- `installer_template.iss` should stay as a stable template.
- [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss) 應保持為穩定模板。
- `build_installer.ps1` generates `installer\build.iss` and passes that generated file to Inno Setup.
- [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1) 會產生 `installer\build.iss`，再把這份生成檔交給 Inno Setup 編譯。

- Stage 3 signing: `make_sign.cmd`
- 第 3 階段：`make_sign.cmd`
- Purpose: sign three files through [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1)
- 作用：透過 [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1) 簽三個發佈檔案
- Signed files / 簽章目標：
- `out\chklink.dist\chklink.exe`
- `out\chklink_cli.exe`
- `installer\<version>\chklink_setup.exe`

## Dev environment tips / 開發環境注意事項

- This repo is Windows-first.
- 本專案以 Windows 環境為主。
- Python files are UTF-8 without BOM.
- Python 檔案使用 UTF-8 無 BOM。
- Markdown files are UTF-8 without BOM.
- Markdown 檔案使用 UTF-8 無 BOM。
- PowerShell and YAML files are UTF-8 without BOM.
- PowerShell 與 YAML 檔案使用 UTF-8 無 BOM。
- `.cmd` files must remain Big5 / cp950.
- `.cmd` 檔必須維持 Big5 / cp950。
- All text files should use CRLF line endings.
- 所有文字檔都應使用 CRLF 換行。
- Be careful with PowerShell text pipelines when editing Traditional Chinese text. They can corrupt file contents.
- 以 PowerShell 文字管線直接處理繁體中文內容時要特別小心，容易造成檔案毀損。

## Code structure / 程式結構

- GUI workflow and UI state: [chklink.py](/D:/pyTest/chkLink/chklink.py)
- GUI 流程與 UI 狀態： [chklink.py](/D:/pyTest/chkLink/chklink.py)
- CLI workflow: [chklink_cli.py](/D:/pyTest/chkLink/chklink_cli.py)
- CLI 流程： [chklink_cli.py](/D:/pyTest/chkLink/chklink_cli.py)
- Shared scan core and Excel report writer: [chklink_core.py](/D:/pyTest/chkLink/chklink_core.py)
- 共用掃描核心與 Excel 報表輸出： [chklink_core.py](/D:/pyTest/chkLink/chklink_core.py)
- Config defaults and parsing: [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)
- 設定預設值與解析： [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)
- Installer generation: [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1)
- Installer 產生流程： [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1)
- Inno Setup template: [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss)
- Inno Setup 範本： [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss)
- Signing flow: [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1)
- 簽章流程： [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1)

## Important project decisions / 重要設計決策

- GUI uses Nuitka `--standalone` because it is more stable for Tk and related runtime assets.
- GUI 使用 Nuitka `--standalone`，因為對 Tk 與相關執行期資源較穩定。
- CLI uses Nuitka `--onefile` because it is more convenient for automation and low-exposure distribution.
- CLI 使用 Nuitka `--onefile`，因為較適合自動化與低曝光分發。
- The installer includes both GUI and CLI, but only GUI gets shortcuts.
- Installer 會同時安裝 GUI 與 CLI，但只為 GUI 建立捷徑。
- Installer output is versioned under `installer\<version>\`.
- Installer 輸出固定放在 `installer\<版本>\`。
- The installer must not include `data\config.yaml` or `data\visited_link.yaml`, to avoid overwriting user settings and cache on upgrade.
- Installer 不可打包 `data\config.yaml` 與 `data\visited_link.yaml`，以免升級時覆蓋使用者設定與快取。
- Auto-update is installer-based, not single-exe replacement based.
- 自動更新採 installer 覆蓋安裝模式，不是單一 exe 替換模式。

## Versioning rules / 版本規則

- Version source of truth: `DEFAULT_APP_VERSION` in [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)
- 版本號唯一來源： [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py) 的 `DEFAULT_APP_VERSION`
- Use three-part versions such as `1.4.0`
- 請使用三段式版本號，例如 `1.4.0`
- Build scripts and installer output paths depend on this version string.
- 建置腳本與 installer 輸出路徑都依賴這個版本字串。

## Scan behavior summary / 掃描行為摘要

- Internal links are validated and recursively scanned.
- 內部連結會檢查有效性並繼續遞迴掃描。
- External links are listed but not recursively validated.
- 外部連結只列出，不做遞迴驗證。
- HTTP links can be reported as insecure depending on config.
- `http://` 連結可依設定列為不安全提醒。
- URL normalization, download detection, soft-404 detection, redirect classification, retry/backoff, and per-domain throttling are implemented in the shared core.
- URL 正規化、下載判定、soft-404、redirect 分類、retry/backoff 與每網域節流都已實作在共用核心。
- Excel reports include an `錯誤類型` column.
- Excel 報表包含 `錯誤類型` 欄位。

## Config and migration notes / 設定與遷移說明

- Runtime config file: `data\config.yaml`
- 執行期設定檔：`data\config.yaml`
- Default config template: [config.yaml-default](/D:/pyTest/chkLink/config.yaml-default)
- 預設設定樣板： [config.yaml-default](/D:/pyTest/chkLink/config.yaml-default)
- Missing config keys are filled by `normalize_setting()` in [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)
- 缺少的設定欄位會由 [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py) 的 `normalize_setting()` 自動補齊。
- Existing users should receive new config keys on next app launch.
- 舊使用者在下次啟動程式時，應自動取得新增的設定欄位。

## Testing instructions / 測試方式

- Python syntax check / Python 語法檢查：
```powershell
python -m py_compile chklink.py chklink_cli.py chklink_config.py chklink_core.py
```

- If you change build or installer flow, re-check:
- 若調整建置或 installer 流程，請重新檢查：
- [make.cmd](/D:/pyTest/chkLink/make.cmd)
- [make_setup.cmd](/D:/pyTest/chkLink/make_setup.cmd)
- [make_sign.cmd](/D:/pyTest/chkLink/make_sign.cmd)
- [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1)
- [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss)
- [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1)

## Editing guidance for agents / 給 agent 的修改指引

- Prefer small, reversible changes.
- 優先採取小而可回復的修改。
- Respect existing scan logic unless the user explicitly asks for behavior changes.
- 除非使用者明確要求改變行為，否則請尊重既有掃描邏輯。
- Do not silently change file encodings.
- 不要默默改變檔案編碼。
- Do not rewrite `.cmd` files as UTF-8.
- 不要把 `.cmd` 檔改寫成 UTF-8。
- If you edit release flow, keep README and AGENTS.md in sync.
- 若修改發佈流程，請同步更新 README 與 AGENTS.md。
- If you rename a user-facing script, update all related docs and wrappers in the same change.
- 若重新命名使用者會直接執行的腳本，請在同一個修改中同步更新所有相關文件與腳本。

## Common tasks / 常見任務入口

- Change scan logic: start with [chklink_core.py](/D:/pyTest/chkLink/chklink_core.py)
- 改掃描邏輯：先看 [chklink_core.py](/D:/pyTest/chkLink/chklink_core.py)
- Change config defaults or version: start with [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)
- 改設定預設值或版本號：先看 [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)
- Change GUI scan flow or log behavior: start with [chklink.py](/D:/pyTest/chkLink/chklink.py)
- 改 GUI 掃描流程或 log 行為：先看 [chklink.py](/D:/pyTest/chkLink/chklink.py)
- Change CLI flow: start with [chklink_cli.py](/D:/pyTest/chkLink/chklink_cli.py)
- 改 CLI 流程：先看 [chklink_cli.py](/D:/pyTest/chkLink/chklink_cli.py)
- Change installer output or packaging: start with [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1) and [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss)
- 改 installer 輸出或封裝：先看 [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1) 與 [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss)
- Change signing flow: start with [make_sign.cmd](/D:/pyTest/chkLink/make_sign.cmd) and [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1)
- 改簽章流程：先看 [make_sign.cmd](/D:/pyTest/chkLink/make_sign.cmd) 與 [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1)
