# chkLink Winget 發佈教學

## 用途

這份文件整理 `chkLink` 提交到 Windows Package Manager Community Repository，也就是 `microsoft/winget-pkgs` 的實際流程，特別補強中文資料較少、但實務上很常卡住的幾個點：

- 為什麼要先 fork
- manifest 要放哪裡
- 版本資料要怎麼準備
- PR 標題與提交方式的大致慣例
- bot / label / checks 出現時代表什麼意思

本文以 `1.4.1` 這一輪的實作經驗為背景撰寫。

## 先記住的核心觀念

- winget 發佈不是「上傳一個安裝檔」而已，而是「提交一組 manifest 到 `microsoft/winget-pkgs`」。
- 你不能直接 push 到 `microsoft/winget-pkgs`，正常流程是先 fork，再從自己的 fork 開分支送 PR。
- winget 不替你代管產物；manifest 只描述安裝來源、版本、雜湊、安裝行為與中繼資料。
- 所以在送 PR 之前，GitHub Release 或其他公開下載位置必須已經準備好，而且網址必須可下載。
- `InstallerUrl`、`InstallerSha256`、版本號、Publisher、PackageIdentifier 彼此要對得起來。
- 依 Microsoft Learn 目前說明，你可以用 `wingetcreate`、`YAMLCreate.ps1`，或手動編寫 manifest。

## chkLink 目前採用的 manifest 結構

以 [`winget\PeterJu\chkLink\1.4.1`](../winget/PeterJu/chkLink/1.4.1) 為例，目前採三個檔案：

- [`PeterJu.chkLink.yaml`](../winget/PeterJu/chkLink/1.4.1/PeterJu.chkLink.yaml)
- [`PeterJu.chkLink.installer.yaml`](../winget/PeterJu/chkLink/1.4.1/PeterJu.chkLink.installer.yaml)
- [`PeterJu.chkLink.locale.zh-TW.yaml`](../winget/PeterJu/chkLink/1.4.1/PeterJu.chkLink.locale.zh-TW.yaml)

這代表目前是「version / installer / locale」拆檔模式。

Microsoft Learn 目前仍說明：

- singleton manifest 只適用於單一 installer 且單一 locale 的簡單情境
- 若要提供較完整的 metadata 與 locale，應改用多檔 manifest
- 多檔 manifest 的最少組成通常是 `version`、`default locale`、`installer` 三檔，其他 locale 再另外追加

`chkLink` 目前採多檔模式，這和官方目前建議的完整 metadata 方向一致。

## 發佈前置條件

在準備 winget PR 之前，建議先確認這幾件事都已完成：

1. 主專案版本號已定稿，例如 `1.4.1`。
2. GitHub Release 已建立完成。
3. 安裝檔下載網址已固定，不會再換。
4. `SHA256` 已重新計算，而且與最終公開下載檔一致。
5. 靜默安裝、靜默卸載、一般安裝至少都已驗證一次。
6. `PackageIdentifier`、`PackageVersion`、`PackageName`、`Publisher` 等欄位與既有套件歷史保持一致。

## 為什麼一定要先 fork

因為 `microsoft/winget-pkgs` 是社群共用倉庫，你通常沒有直接寫入權限。標準流程是：

1. fork `microsoft/winget-pkgs` 到自己的 GitHub 帳號
2. 把 fork clone 到本機
3. 在 fork 的分支上新增或更新 manifest
4. 從 fork 對上游 `microsoft/winget-pkgs` 發 PR

對 `chkLink` 而言，交接文件記錄的本機 fork 工作目錄是：

- `winget-pkgs`

## 實際操作順序

### 1. 先同步自己的 fork

如果 fork 很久沒更新，先同步再開新版分支，否則容易一開始就帶入不必要差異。

### 2. 建立本次版本分支

分支名稱通常可讀即可，例如：

```text
add-peterju-chklink-1.4.1
```

### 3. 準備對應版本資料夾

在 `winget-pkgs` 中，manifest 路徑依 `PackageIdentifier` 與版本號分層。對 `PeterJu.chkLink` 來說，目標會是：

```text
manifests\p\PeterJu\chkLink\1.4.1\
```

### 4. 更新 manifest 內容

至少要檢查：

- `PackageIdentifier`
- `PackageVersion`
- `PackageName`
- `Publisher`
- `InstallerUrl`
- `InstallerSha256`
- `InstallerType`
- 靜默安裝 / 靜默卸載參數
- locale 描述文字

若要依官方工具流程建立 manifest，也可以考慮：

```powershell
winget install wingetcreate
wingetcreate new
```

Microsoft Learn 目前說明 `wingetcreate new` 會一步步詢問欄位，最後也能直接協助提交到 packages repository。對於第一次送件的人，這比完全手寫 YAML 更不容易漏欄位。

### 5. 本機先驗證 manifest

在送 PR 之前，建議至少先做這兩類檢查：

```powershell
winget validate --manifest <manifest 資料夾或檔案路徑>
winget install --manifest <manifest 資料夾或檔案路徑>
```

原因很直接：

- `winget validate` 可先抓出 schema 或欄位問題
- `winget install --manifest` 可先檢查安裝器、silent switch、下載與安裝流程是否真的可行

## PR 標題大致長什麼樣子

從 `winget-pkgs` 公開 PR 列表可看到，常見標題格式有：

- `New version: Package.Identifier version x.y.z`
- `New package: Package.Identifier version x.y.z`

對已存在的 `chkLink` 套件來說，通常會落在「New version」這一類。

即使你用的是 `wingetcreate` 或其他工具，自動產生的 PR 標題也多半會接近這個格式。

另外，`winget-pkgs` 公開 PR 列表目前常見的 label 包括：

- `New-Manifest`
- `New-Package`
- `Azure-Pipeline-Passed`
- `Validation-Completed`
- `Needs-Author-Feedback`
- `Error-Hash-Mismatch`
- `Validation-Installation-Error`

但要注意：

- label 是由 repo 流程與 bot 自動加上的結果，不是你在 PR 表單中手動填的固定欄位
- 新 package 與既有 package 更新，看到的 label 組合可能不同
- 官方網站 UI 與 label 細節可能會調整，所以教學應以「理解其意義」為主，不要背單一畫面長相

## `chkLink` 實際使用過的 PR 內容範例

以下內容整理自 `microsoft/winget-pkgs` 的 `#351979`，可作為後續版本提交時的實際參考。

### PR title

```text
New version: PeterJu.chkLink 1.4.1
```

### PR body

下面這段保留實際送出的英文原文，方便之後對照 GitHub PR 畫面與既有提交習慣：

```text
## Summary

- Add PeterJu.chkLink version 1.4.1
- Installer type: Inno Setup
- Architecture: x64
- Silent install and silent uninstall have been verified

## Release

- https://github.com/peterju/chkLink/releases/tag/v1.4.1

## Notes

- Installer asset: chklink-1.4.1-win-x64-setup.exe
- Silent install switch: /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-
- Silent uninstall was tested with unins000.exe
- User-owned runtime files are stored under %LOCALAPPDATA%\chkLink\data\
- Uninstall removes the installation directory cleanly while preserving user-owned runtime files
```

### 為什麼這樣寫

- `Summary`：讓 reviewer 一眼知道你提交的是新版本、安裝器類型、架構與是否完成靜默安裝驗證。
- `Release`：直接給 GitHub Release 連結，方便 bot 或 reviewer 追下載檔案來源。
- `Notes`：補足 manifest 難以完整表達、但 reviewer 很在意的實測與安裝行為資訊。

### 後續版本可沿用的 PR 範本

```text
## Summary

- Add PeterJu.chkLink version <version>
- Installer type: Inno Setup
- Architecture: x64
- Silent install and silent uninstall have been verified

## Release

- https://github.com/peterju/chkLink/releases/tag/v<version>

## Notes

- Installer asset: chklink-<version>-win-x64-setup.exe
- Silent install switch: /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-
- Silent uninstall was tested with unins000.exe
- User-owned runtime files are stored under %LOCALAPPDATA%\chkLink\data\
- Uninstall removes the installation directory cleanly while preserving user-owned runtime files
```

## checks 與 bot 常見訊號

### CLA

第一次向 Microsoft 倉庫送 PR 時，CLA bot 會檢查你是否已完成 Contributor License Agreement。

看到這類訊息時，意思通常是：

- 需要你按指示完成一次 CLA
- 完成後，後續同帳號在 Microsoft 其他 repo 通常不必重簽

### Azure-Pipeline-Passed

這通常表示自動化驗證流程已通過。

但它不保證一定會立刻 merge，因為：

- 仍可能需要人工 review
- 仍可能有其他政策或排程上的等待

### `wingetbot` 留下 Validation Pipeline Run

你這次 PR 中看到的是：

```text
Validation Pipeline Run WinGetSvc-Validation-136-351979-20260325-1
```

這代表：

- bot 已替這個 PR 啟動驗證流程
- 後面的連結會帶你到 Azure Pipeline 結果頁
- 如果 reviewer 要你查失敗原因，通常就要先看這個 pipeline

若這則 comment 搭配 PR 頁面顯示 `Checks passing`，通常表示目前自動驗證沒有卡住。

### Validation-Completed / Validation passed

通常表示 manifest 結構、下載、安裝測試等主要驗證已經通過。

### Needs-Author-Feedback

這代表目前卡點在作者這邊，通常需要你回應、修正或解釋。

常見原因包括：

- 安裝失敗
- 雜湊不一致
- URL 失效或下載內容改變
- 套件資訊疑似重複
- bot 或 reviewer 提出修正要求

### Error-Hash-Mismatch

這表示 manifest 內的 `InstallerSha256` 與實際下載到的檔案不一致。

最常見原因是：

- 你在算 hash 後，又重新上傳了安裝檔
- CDN 還沒完全刷新
- 指到的不是最終正式檔

### Validation-Installation-Error

這通常代表自動驗證機器實際安裝時失敗。要優先檢查：

- 安裝程式是否真的支援靜默安裝
- 靜默安裝參數是否正確
- 安裝需要的相依條件是否在乾淨機器上成立
- 安裝器是不是會跳授權、UAC、重開機提示或其他互動畫面

## `chkLink` 這個專案特別要注意的地方

1. winget 用的是公開下載檔案，不是組織內部更新站。
2. `PackageName` 目前已定為 `chkLink`，不要隨意改成中文全名。
3. locale 描述可以用中文，但識別欄位要與既有套件歷史一致。
4. 若版本已升到 `1.4.1`，就不要回頭讓 `1.4.0` 指向新的 installer。
5. 版本號、安裝檔內容、GitHub Release、winget manifest 必須彼此一致。

## 建議提交前自我檢查

1. 下載 `InstallerUrl` 指向的檔案，確認能正常開啟。
2. 重新計算該檔案的 `SHA256`。
3. 確認 PR 中只包含本次版本需要的 manifest。
4. 確認資料夾路徑與檔名拼字完全正確。
5. 確認靜默安裝與靜默卸載參數已實測。
6. 確認 GitHub Release 沒有再被替換成不同內容的同名檔案。
7. 確認同一個 `PackageIdentifier + PackageVersion` 沒有另一個未關閉 PR，避免和既有提交互相衝突。
8. 若是社群協助型流程，也可視情況先開 `Package Request/Submission` issue；但這不是每次更新版本都必做。

## 建議保存的觀念

### 1. 先有公開下載檔案，再送 winget

如果 Release 還沒穩定，先不要急著送 PR。因為 winget 驗證會直接抓你提供的 URL。

### 2. 不要重寫舊版本的 Release 內容去配合新 manifest

已公開的版本應維持版本號與產物一致。修正行為時，應該升 patch 版號，例如 `1.4.0 -> 1.4.1`。

### 3. checks 過了，不代表立刻 merge

winget-pkgs 是大型社群倉庫，通過自動檢查後，仍可能需要等待 reviewer 或排隊。

## 官方參考

- Microsoft Learn: [Submit packages to Windows Package Manager](https://learn.microsoft.com/en-us/windows/package-manager/package/)
- Microsoft Learn: [validate command (winget)](https://learn.microsoft.com/en-us/windows/package-manager/winget/validate)
- Microsoft Learn: [Create your package manifest](https://learn.microsoft.com/en-us/windows/package-manager/package/manifest)
- GitHub: [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs)
