# chkLink GitHub Release 教學

## 用途

這份文件說明 `chkLink` 主專案如何建立 GitHub Release，並整理「版本號 / tag / Release / Local repo / GitHub repo」之間最容易混淆的同步觀念。

本文以 `1.4.1` 這一輪的實際流程為背景撰寫，並以專案根目錄為工作目錄。

## 先記住的核心觀念

- GitHub Release 是建立在 Git tag 之上的。
- 先有 tag，才會有對應 Release。
- 在 GitHub 網站建立 Release 時，如果順手建立了新 tag，本質上等於「在遠端建立一個新的 Git tag」。
- 遠端新建的 tag 不會自動出現在你的本機 repo；本機必須再做同步。
- `pull` 主要同步 branch；若你是從網站建立 tag，實務上建議直接做 `git fetch --tags origin`，比單純 `git pull` 更精準。
- 若 Release 指向的 commit 也是本機尚未抓下來的新內容，才再補 `git pull origin main`。

## 本專案的 Release 與更新來源分工

- GitHub Release 主要是對外公開下載使用。
- 程式內建更新來源預設仍以組織內部發佈站為主。
- 不要把 `release\<version>\...` 誤當成 GUI 預設更新來源。
- 本專案對外整理 GitHub Release 發佈檔案（assets）的腳本是 [`make_github_release.cmd`](../make_github_release.cmd)。

## 建立 Release 前的前置確認

在建立 GitHub Release 前，先確認這幾件事：

1. [`chklink_config.py`](../chklink_config.py) 的 `DEFAULT_APP_VERSION` 已是目標版本。
2. `main` 已包含本次版本要公開的 commit。
3. 本機工作樹乾淨，避免把未完成內容誤認為已發佈狀態。
4. `installer\<version>\` 內的安裝檔、`RemoteVersion.yaml`、`SHA256.txt` 已準備完成。
5. `release\<version>\` 內的 GitHub Release 發佈檔案（assets）已由 [`make_github_release.cmd`](../make_github_release.cmd) 整理完成。
6. 先確認 `origin/main` 與本機 `main` 一致，再去網站建立 Release。

可先用這幾個指令確認：

```powershell
git status --short --branch
git rev-parse HEAD
git ls-remote origin refs/heads/main
git tag -l
```

## 建立 GitHub Release 的建議流程

### 做法 A：先在本機建立 tag，再 push

這是最不容易混淆的一種方式。

1. 確認目前 `HEAD` 就是你要發佈的 commit。
2. 在本機建立 tag，例如：

```powershell
git tag v1.4.1
git push origin main
git push origin v1.4.1
```

3. 到 GitHub 專案頁面開 `Releases`。
4. 建立新 Release 時，直接選既有 tag `v1.4.1`。
5. 上傳 `release\1.4.1\` 內整理好的對外發佈檔案（assets）。

優點是 tag 的建立點完全由本機掌握，Local 與 GitHub 比較不容易出現「網站上有 tag，但本機還沒抓到」的認知落差。

### 做法 B：直接在 GitHub 網站建立 Release 並同時建立新 tag

GitHub 官方文件允許你在 Release 表單中直接輸入版本號並建立新 tag。

流程大致如下：

1. 進入 GitHub repo 的 `Releases` 頁面。
2. 點 `Draft a new release`。
3. 在 `Choose a tag` 輸入例如 `v1.4.1`。
4. GitHub 會讓你建立新 tag。
5. 選擇 `Target`，通常是 `main`。
6. 若 GitHub 畫面有顯示 `Previous tag`，可選前一版 tag，讓 GitHub 比較版本差異或產生 release notes。
7. 填寫 Release title 與說明；若只是想先用 GitHub 自動產生摘要，也可以按 `Generate release notes` 再手動調整。
8. 上傳安裝檔與發佈檔案（assets）。
9. 依需要選擇 `This is a pre-release` 或 `Set as latest release`。
10. 若只是先整理內容，先存成 draft；確認檔案都齊全後再正式發佈。

這個做法很方便，但要特別記住：

- 這個新 tag 是先出現在 GitHub 遠端。
- 你的本機 repo 不會自動知道它存在。
- 發佈完成後，請回本機做同步。

## GitHub 網站目前常見的 Release 欄位

依 GitHub 官方目前的說明，建立 Release 時常見欄位與選項包括：

- `Choose a tag`：選既有 tag，或直接建立新 tag。
- `Target`：當你新建 tag 時，指定它要落在哪個 branch / commit 線上。
- `Previous tag`：可選前一版 tag，讓 GitHub 比對版本差異。
- `Release title`：給使用者看的標題。
- `Describe this release`：Release 說明文字。
- `Generate release notes`：由 GitHub 自動產生摘要，再由你手動調整。
- 檔案上傳區（binaries / assets）：放安裝檔、雜湊檔、版本資訊等檔案。
- `This is a pre-release`：標記為預發版本。
- `Set as latest release`：手動指定為最新版本；若不選，GitHub 會依版本規則自動判斷。
- `Save draft` / `Publish release`：可先存草稿，再正式公開。

如果未來 GitHub 網站的按鈕位置或細部文案有微調，優先以官方頁面實際顯示為準，但上述概念通常不會一起消失。

## `chkLink` 實際使用過的 Release 內容範例

以下內容整理自 `v1.4.1` 已發佈 Release，可作為後續版本的撰寫基礎。

### Release title

```text
v1.4.1
```

### Release body

```text
## 本版重點

- 修正安裝於 Program Files 時，非系統管理員權限下掃描完成後可能無法正常收尾的問題
- 使用者資料改存到 %LOCALAPPDATA%\chkLink\data\
- update.cmd 改放安裝根目錄
- 掃描完成後即使快取寫入失敗，也會先恢復 UI 狀態並顯示提示
- 驗證 silent install / silent uninstall 均可正常完成，且安裝目錄不殘留程式內容

## 下載檔案

- chklink-1.4.1-win-x64-setup.exe：Windows x64 安裝版
- chklink-1.4.1-RemoteVersion.yaml：版本資訊
- chklink-1.4.1-SHA256.txt：雜湊驗證檔

## 注意事項

- 首次下載執行時，Windows SmartScreen 或 Smart App Control 仍可能出現提示。
- 若此版本已確認穩定，且仍遭 Microsoft 防護機制誤判，可再提交檔案到 https://www.microsoft.com/en-us/wdsi/filesubmission 回報，或直接關閉系統的「智慧型應用程式控制」。
- 本工具的主要用途是網站失效連結掃描、外部連結列出、圖片 alt 檢查與報表輸出。
- GUI 預設更新來源仍建議使用組織內部發佈站；GitHub Release 主要提供對外公開下載。

## SHA256 驗證

請參考 chklink-1.4.1-SHA256.txt 。
```

### 這份 Release 文案的寫法重點

- `本版重點`：只寫對使用者或維護者真的重要的變更，不要把所有內部重構都貼上去。
- `下載檔案`：直接列出各檔案用途，讓使用者不用猜該下載哪一個檔案。
- `注意事項`：用來提醒 SmartScreen、更新來源分工、回報誤判方式等容易被問到的事情。
- `SHA256 驗證`：明確告訴使用者去哪裡看雜湊資訊。

### 後續版本可沿用的 Release 範本

```text
## 本版重點

- 
- 
- 

## 下載檔案

- chklink-<version>-win-x64-setup.exe：Windows x64 安裝版
- chklink-<version>-RemoteVersion.yaml：版本資訊
- chklink-<version>-SHA256.txt：雜湊驗證檔

## 注意事項

- 首次下載執行時，Windows SmartScreen 或 Smart App Control 仍可能出現提示。
- 若此版本已確認穩定，且仍遭 Microsoft 防護機制誤判，可再提交檔案到 https://www.microsoft.com/en-us/wdsi/filesubmission 回報。
- GUI 預設更新來源仍建議使用組織內部發佈站；GitHub Release 主要提供對外公開下載。

## SHA256 驗證

請參考 chklink-<version>-SHA256.txt 。
```

## 建完 Release 後，本機要怎麼同步

如果 tag 是在 GitHub 網站上建立的，建議至少執行：

```powershell
git fetch --tags origin
```

若你也懷疑遠端 `main` 有新 commit，而本機還沒同步，再補：

```powershell
git pull origin main
```

同步後，可這樣確認：

```powershell
git tag -l v1.4.1
git ls-remote origin refs/tags/v1.4.1
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

判讀方式：

- `git tag -l v1.4.1` 有結果，代表本機已看得到該 tag。
- `git ls-remote origin refs/tags/v1.4.1` 有結果，代表 GitHub 遠端有該 tag。
- 若 `git rev-parse HEAD` 與 `git ls-remote origin refs/heads/main` 的 commit 相同，代表本機 `main` 與 GitHub `main` 一致。

## 常見誤解

### 誤解 1：在 GitHub 網站按了 Release，Local 就會同步

不會。GitHub 網站上的 Release / tag 變更，不會主動回寫到你本機的 `.git`。

### 誤解 2：只要 `git pull` 就一定會把所有 tag 拉回來

實務上不要這樣假設。對「網站上新建 tag」這件事，最穩妥的是直接執行 `git fetch --tags origin`。

### 誤解 3：GitHub Release 就是程式內自動更新來源

對 `chkLink` 不是。依目前專案規則，GitHub Release 與程式內更新來源是分開的兩條線。

## 這個專案的建議操作順序

1. 完成程式修改與驗證。
2. 確認版本號已升級。
3. 完成 build、sign、setup、SHA256、GitHub Release 發佈檔案整理（assets）。
4. 確認本機 `main` 與 `origin/main` 一致。
5. 建立 `v<version>` tag。
6. 建立 GitHub Release。
7. 若 tag 是在網站建立的，回本機做 `git fetch --tags origin`。
8. 再次確認 Local / remote / tag 一致。

## 建議保留的檢查指令

```powershell
git status --short --branch
git branch -vv
git rev-parse HEAD
git ls-remote origin refs/heads/main
git tag -l
git ls-remote origin refs/tags/v1.4.1
```

## 官方參考

- GitHub Docs: [Managing releases in a repository](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- GitHub Docs: [About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
