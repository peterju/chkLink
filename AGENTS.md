# AGENTS.md

## Project overview / 專案概要

- This is a Windows website link-checking project with two entry points.
- 這是一個 Windows 網站失效連結掃描專案，提供兩個入口。
- For current progress, in-flight tasks, and handoff status, read [HANDOFF.md](HANDOFF.md) first.
- 若要了解目前工作進度、進行中的任務與交接狀態，請先看 [HANDOFF.md](HANDOFF.md)。
- `HANDOFF.md` is a living handoff file for the next maintainer / agent and should be updated as progress changes.
- [HANDOFF.md](HANDOFF.md) 是給下一位維護者 / agent 使用的動態交接檔，應隨目前進度變化持續更新。
- If `HANDOFF.md` contains a `決策紀錄` section, read it before proposing alternative implementations.
- 若 [HANDOFF.md](HANDOFF.md) 內有 `決策紀錄` 章節，請先讀完再提出替代方案，避免重複討論已排除的路線。
- GUI: [chklink.py](chklink.py)
- CLI: [chklink_cli.py](chklink_cli.py)
- The main product is the GUI. The CLI is intentionally low-profile and is mainly for automation, scheduling, and debugging.
- 主要產品是 GUI；CLI 採低曝光設計，主要提供自動化、排程與除錯用途。
- The scan core is shared by both entry points and lives in [chklink_core.py](chklink_core.py).
- GUI 與 CLI 共用同一套掃描核心，位於 [chklink_core.py](chklink_core.py)。
- Runtime constants, versioning, config defaults, update URLs, and migration helpers live in [chklink_config.py](chklink_config.py).
- 執行期常數、版本號、預設設定、更新網址與遷移輔助都集中在 [chklink_config.py](chklink_config.py)。

## Build and release commands / 建置與發佈指令

- Stage 1 build: `make_exec.cmd`
- 第 1 階段：`make_exec.cmd`
- Purpose: compile GUI and CLI, ensure `update.cmd`, and write `installer\<version>\RemoteVersion.yaml`
- 作用：編譯 GUI 與 CLI，確保 `update.cmd` 存在，並產生 `installer\<版本>\RemoteVersion.yaml`
- GUI output: `out\chklink.dist\chklink.exe`
- GUI 輸出：`out\chklink.dist\chklink.exe`
- CLI output: `out\chklink_cli.exe`
- CLI 輸出：`out\chklink_cli.exe`

- Stage 2 app signing: `make_sign_app.cmd`
- 第 2 階段：`make_sign_app.cmd`
- Purpose: sign `out\chklink.dist\chklink.exe` and `out\chklink_cli.exe` through [sign_files.ps1](sign_files.ps1) with `-Target app`
- 作用：透過 [sign_files.ps1](sign_files.ps1) 搭配 `-Target app` 對 `out\chklink.dist\chklink.exe` 與 `out\chklink_cli.exe` 加簽

- Stage 3 setup packaging: `make_setup.cmd`
- 第 3 階段：`make_setup.cmd`
- Purpose: build `installer\<version>\chklink_setup.exe` through [build_setup.ps1](build_setup.ps1) and [installer_template.iss](installer_template.iss)
- 作用：透過 [build_setup.ps1](build_setup.ps1) 與 [installer_template.iss](installer_template.iss) 產生 `installer\<版本>\chklink_setup.exe`
- `installer_template.iss` should stay as a stable template.
- [installer_template.iss](installer_template.iss) 應保持為穩定模板。
- `build_setup.ps1` generates `installer\build.iss` and passes that generated file to Inno Setup.
- [build_setup.ps1](build_setup.ps1) 會產生 `installer\build.iss`，再把這份生成檔交給 Inno Setup 編譯。

- Stage 4 setup signing: `make_sign_setup.cmd`
- 第 4 階段：`make_sign_setup.cmd`
- Purpose: sign `installer\<version>\chklink_setup.exe` through [sign_files.ps1](sign_files.ps1) with `-Target setup`
- 作用：透過 [sign_files.ps1](sign_files.ps1) 搭配 `-Target setup` 對 `installer\<版本>\chklink_setup.exe` 加簽
- `installer\<version>\chklink_setup.exe`

- Optional checksum step: `make_sha256.cmd`
- 可選雜湊步驟：`make_sha256.cmd`
- Purpose: generate `installer\<version>\SHA256.txt` for `chklink_setup.exe` and `RemoteVersion.yaml`
- 作用：為 `chklink_setup.exe` 與 `RemoteVersion.yaml` 產生 `installer\<版本>\SHA256.txt`

- Optional GitHub Release packaging step: `make_github_release.cmd`
- 可選 GitHub Release 整理步驟：`make_github_release.cmd`
- Purpose: prepare versioned public-release files (assets) under `release\<version>\`
- 作用：在 `release\<版本>\` 下整理對外公開發佈用的版本化檔案（assets）

- Interactive menu: `menu.cmd`
- 互動式選單：`menu.cmd`
- Purpose: present steps `1 / 2 / 3 / 4 / 5 / 6` for manual release operations
- 作用：提供 `1 / 2 / 3 / 4 / 5 / 6` 的選單入口，方便依序手動執行建置流程

## Current release workflow / 目前發佈流程

- Recommended order: `make_exec.cmd -> make_sign_app.cmd -> make_setup.cmd -> make_sign_setup.cmd`
- 建議順序：`make_exec.cmd -> make_sign_app.cmd -> make_setup.cmd -> make_sign_setup.cmd`
- `menu.cmd` is only a menu wrapper. It is not the actual compile step.
- `menu.cmd` 只是選單入口，不是實際的編譯步驟。
- `make_github_release.cmd` is also optional and should run only after installer files (assets) already exist.
- `make_github_release.cmd` 也是可選步驟，而且應在 installer 相關檔案（assets）都已完成後再執行。
- Upload order matters: upload `chklink_setup.exe` first, then update `RemoteVersion.yaml`.
- 上傳順序很重要：先上傳 `chklink_setup.exe`，再更新 `RemoteVersion.yaml`。
- GitHub Release preparation is separate from the in-app update source.
- GitHub Release 檔案整理（assets）應與程式內更新來源分離處理。

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

- GUI workflow and UI state: [chklink.py](chklink.py)
- GUI 流程與 UI 狀態： [chklink.py](chklink.py)
- CLI workflow: [chklink_cli.py](chklink_cli.py)
- CLI 流程： [chklink_cli.py](chklink_cli.py)
- Shared scan core and Excel report writer: [chklink_core.py](chklink_core.py)
- 共用掃描核心與 Excel 報表輸出： [chklink_core.py](chklink_core.py)
- Config defaults and parsing: [chklink_config.py](chklink_config.py)
- 設定預設值與解析： [chklink_config.py](chklink_config.py)
- Installer generation: [build_setup.ps1](build_setup.ps1)
- Installer 產生流程： [build_setup.ps1](build_setup.ps1)
- Inno Setup template: [installer_template.iss](installer_template.iss)
- Inno Setup 範本： [installer_template.iss](installer_template.iss)
- Signing flow: [sign_files.ps1](sign_files.ps1)
- 簽章流程： [sign_files.ps1](sign_files.ps1)

## Important project decisions / 重要設計決策

- GUI uses Nuitka `--standalone` because it is more stable for Tk and related runtime files/resources.
- GUI 使用 Nuitka `--standalone`，因為對 Tk 與相關執行期檔案 / 資源較穩定。
- CLI uses Nuitka `--onefile` because it is more convenient for automation and low-exposure distribution.
- CLI 使用 Nuitka `--onefile`，因為較適合自動化與低曝光分發。
- The installer includes both GUI and CLI, but only GUI gets shortcuts.
- Installer 會同時安裝 GUI 與 CLI，但只為 GUI 建立捷徑。
- Installer output is versioned under `installer\<version>\`.
- Installer 輸出固定放在 `installer\<版本>\`。
- The installer must not include user-owned `config.yaml` or `visited_link.yaml`, to avoid overwriting user settings and cache on upgrade.
- Installer 不可打包使用者持有的 `config.yaml` 與 `visited_link.yaml`，以免升級時覆蓋使用者設定與快取。
- The running app version must come from `DEFAULT_APP_VERSION`, not from `data\LocalVersion.yaml`.
- 執行中的程式版本必須以 `DEFAULT_APP_VERSION` 為準，不再依賴 `data\LocalVersion.yaml`。
- Auto-update is installer-based, not single-exe replacement based.
- 自動更新採 installer 覆蓋安裝模式，不是單一 exe 替換模式。

## Versioning rules / 版本規則

- Version source of truth: `DEFAULT_APP_VERSION` in [chklink_config.py](chklink_config.py)
- 版本號唯一來源： [chklink_config.py](chklink_config.py) 的 `DEFAULT_APP_VERSION`
- Use three-part versions such as `1.4.0`
- 請使用三段式版本號，例如 `1.4.0`
- The project follows Semantic Versioning in spirit, but the compatibility surface is the desktop tool behavior rather than a Python library API.
- 本專案採用 Semantic Versioning 精神，但相容性判斷以桌面工具的對外行為為準，不是以 Python 函式庫 API 為準。
- Treat GUI / CLI usage, config format, report format, update flow, and release file naming as the effective public interface.
- 請將 GUI / CLI 使用方式、設定格式、報表格式、更新流程與發佈檔名視為實際的公開介面。
- Build scripts and installer output paths depend on this version string.
- 建置腳本與 installer 輸出路徑都依賴這個版本字串。
- `RemoteVersion.yaml` is the only release version file that should be uploaded to the download server.
- 上傳到下載伺服器的版本檔只保留 `RemoteVersion.yaml`。

## Source of truth / 真相來源

- Runtime app version: `DEFAULT_APP_VERSION` in [chklink_config.py](chklink_config.py)
- 執行中的程式版本： [chklink_config.py](chklink_config.py) 的 `DEFAULT_APP_VERSION`
- Remote update version file: `installer\<version>\RemoteVersion.yaml`
- 遠端更新版本檔：`installer\<版本>\RemoteVersion.yaml`
- Public GitHub Release files (assets): `release\<version>\chklink-<version>-win-x64-setup.exe`, `release\<version>\chklink-<version>-RemoteVersion.yaml`, `release\<version>\chklink-<version>-SHA256.txt`
- 對外 GitHub Release 檔案（assets）：`release\<版本>\chklink-<version>-win-x64-setup.exe`、`release\<版本>\chklink-<version>-RemoteVersion.yaml`、`release\<版本>\chklink-<version>-SHA256.txt`
- User-owned runtime files: `%LOCALAPPDATA%\chkLink\data\config.yaml`, `%LOCALAPPDATA%\chkLink\data\visited_link.yaml`
- 使用者持有的執行期檔案：`%LOCALAPPDATA%\chkLink\data\config.yaml`、`%LOCALAPPDATA%\chkLink\data\visited_link.yaml`
- App-owned runtime helper: `update.cmd`
- 程式持有的執行期輔助檔：`update.cmd`
- Do not reintroduce `data\LocalVersion.yaml` as a version source.
- 不要再把 `data\LocalVersion.yaml` 帶回版本真相來源。
- Do not treat `release\<version>\...` files (assets) as the default in-app update source unless the user explicitly asks to switch to GitHub-hosted updates.
- 除非使用者明確要求改成 GitHub 更新來源，否則不要把 `release\<版本>\...` 檔案（assets）當成 GUI 預設更新來源。

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

- Runtime config file: `%LOCALAPPDATA%\chkLink\data\config.yaml`
- 執行期設定檔：`%LOCALAPPDATA%\chkLink\data\config.yaml`
- Default config template: [config.yaml-default](config.yaml-default)
- 預設設定樣板： [config.yaml-default](config.yaml-default)
- Missing config keys are filled by `normalize_setting()` in [chklink_config.py](chklink_config.py)
- 缺少的設定欄位會由 [chklink_config.py](chklink_config.py) 的 `normalize_setting()` 自動補齊。
- Existing users should receive new config keys on next app launch.
- 舊使用者在下次啟動程式時，應自動取得新增的設定欄位。
- User-owned runtime files must stay in a writable per-user location, not under `Program Files`.
- 使用者持有的執行期檔案必須放在每位使用者可寫的位置，不可再寫回 `Program Files`。
- `update.cmd` remains under the install directory root because it is app-owned and used by the in-app updater.
- `update.cmd` 仍保留在安裝目錄根目錄，因為它是程式持有的更新輔助檔。
- Default headers must not contain real cookies, tokens, or authenticated session data.
- 預設 headers 不可包含真實 cookie、token 或已登入的 session 資料。

## Do Not Commit / 不可提交項目

- Do not commit `%LOCALAPPDATA%\chkLink\data\config.yaml` or `%LOCALAPPDATA%\chkLink\data\visited_link.yaml`.
- 不要提交 `%LOCALAPPDATA%\chkLink\data\config.yaml` 或 `%LOCALAPPDATA%\chkLink\data\visited_link.yaml`。
- Do not commit real cookies, Authorization headers, tokens, passwords, or private release credentials.
- 不要提交真實 cookie、Authorization header、token、密碼或私有發佈憑證資訊。
- Be cautious with `sign_files.ps1`; the thumbprint may be environment-specific and should not silently become a portable secret/config dependency.
- 請特別注意 [sign_files.ps1](sign_files.ps1)；其中的 thumbprint 具有環境相依性，不應默默演變成可攜式祕密或必要設定。

## Testing instructions / 測試方式

- Python syntax check / Python 語法檢查：
```powershell
python -m py_compile chklink.py chklink_cli.py chklink_config.py chklink_core.py
```

- If you change build or installer flow, re-check:
- 若調整建置或 installer 流程，請重新檢查：
- [make_exec.cmd](make_exec.cmd)
- [menu.cmd](menu.cmd)
- [make_sign_app.cmd](make_sign_app.cmd)
- [make_setup.cmd](make_setup.cmd)
- [make_sign_setup.cmd](make_sign_setup.cmd)
- [make_sha256.cmd](make_sha256.cmd)
- [make_github_release.cmd](make_github_release.cmd)
- [build_setup.ps1](build_setup.ps1)
- [installer_template.iss](installer_template.iss)
- [sign_files.ps1](sign_files.ps1)

## Validation checklist / 驗證清單

- If you change scan logic, run the Python syntax check and verify at least one real scan flow in GUI or CLI.
- 若修改掃描邏輯，請至少執行 Python 語法檢查，並實際驗證一次 GUI 或 CLI 的掃描流程。
- If you change update logic, verify GUI version display, remote version comparison, and `update.cmd` launch behavior.
- 若修改更新流程，請檢查 GUI 版本顯示、遠端版本比較，以及 `update.cmd` 啟動 installer 的行為。
- If you change build/release flow, verify script names, output paths, installer contents, and README/AGENTS consistency.
- 若修改建置或發佈流程，請檢查腳本名稱、輸出路徑、installer 內容，以及 README / AGENTS 是否一致。
- If you change GitHub Release packaging, verify both `installer\<version>\` and `release\<version>\` outputs and confirm naming still matches README.
- 若修改 GitHub Release 整理流程，請同時檢查 `installer\<版本>\` 與 `release\<版本>\` 的輸出，並確認檔名仍與 README 一致。
- If you touch `.cmd` files, preserve cp950 encoding and CRLF line endings.
- 若修改 `.cmd` 檔，請維持 cp950 編碼與 CRLF 換行。

## Known sharp edges / 已知易踩點

- PowerShell text pipelines can corrupt Traditional Chinese text when rewriting files.
- PowerShell 文字管線在重寫檔案時可能破壞繁體中文內容。
- `.cmd` files are not UTF-8 in this repo.
- 本專案的 `.cmd` 檔不是 UTF-8。
- `menu.cmd` is the menu, while `make_exec.cmd` is the actual compile step.
- `menu.cmd` 是選單，`make_exec.cmd` 才是實際編譯步驟。
- `make_github_release.cmd` copies assets from `installer\<version>\` into `release\<version>\`; it does not rename or replace the installer-side files.
- `make_github_release.cmd` 會把 `installer\<版本>\` 的檔案（assets）複製整理到 `release\<版本>\`，不會直接改名或覆蓋 installer 那邊的原檔。
- Uploading `RemoteVersion.yaml` too early can expose a new version before the installer is reachable.
- 若過早上傳 `RemoteVersion.yaml`，會在 installer 尚未可下載時提前暴露新版本。

## Editing guidance for agents / 給 agent 的修改指引

- Prefer small, reversible changes.
- 優先採取小而可回復的修改。
- Respect existing scan logic unless the user explicitly asks for behavior changes.
- 除非使用者明確要求改變行為，否則請尊重既有掃描邏輯。
- After completing a change, review whether README.md, AGENTS.md, and HANDOFF.md need to be updated in the same round.
- 完成變更後，請回頭檢查 README.md、AGENTS.md、HANDOFF.md 是否需要在同一輪一併更新。
- Do not silently change file encodings.
- 不要默默改變檔案編碼。
- Do not rewrite `.cmd` files as UTF-8.
- 不要把 `.cmd` 檔改寫成 UTF-8。
- If you edit release flow, keep README and AGENTS.md in sync.
- 若修改發佈流程，請同步更新 README 與 AGENTS.md。
- If you rename a user-facing script, update all related docs and wrappers in the same change.
- 若重新命名使用者會直接執行的腳本，請在同一個修改中同步更新所有相關文件與腳本。

## Common tasks / 常見任務入口

- Change scan logic: start with [chklink_core.py](chklink_core.py)
- 改掃描邏輯：先看 [chklink_core.py](chklink_core.py)
- Change config defaults or version: start with [chklink_config.py](chklink_config.py)
- 改設定預設值或版本號：先看 [chklink_config.py](chklink_config.py)
- Change GUI scan flow or log behavior: start with [chklink.py](chklink.py)
- 改 GUI 掃描流程或 log 行為：先看 [chklink.py](chklink.py)
- Change CLI flow: start with [chklink_cli.py](chklink_cli.py)
- 改 CLI 流程：先看 [chklink_cli.py](chklink_cli.py)
- Change installer output or packaging: start with [build_setup.ps1](build_setup.ps1) and [installer_template.iss](installer_template.iss)
- 改 installer 輸出或封裝：先看 [build_setup.ps1](build_setup.ps1) 與 [installer_template.iss](installer_template.iss)
- Change signing flow: start with [make_sign_app.cmd](make_sign_app.cmd), [make_sign_setup.cmd](make_sign_setup.cmd), and [sign_files.ps1](sign_files.ps1)
- 改簽章流程：先看 [make_sign_app.cmd](make_sign_app.cmd)、[make_sign_setup.cmd](make_sign_setup.cmd) 與 [sign_files.ps1](sign_files.ps1)
