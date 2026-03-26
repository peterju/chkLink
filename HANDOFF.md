# HANDOFF

## 用途

這份文件用來記錄「目前工作進度、已完成事項、未完成事項、外部 PR 狀態」。

- 穩定規則、專案結構、編碼與發佈原則請看 [AGENTS.md](AGENTS.md)
- 當前進度、待辦與交接重點請先看這份 [HANDOFF.md](HANDOFF.md)
- 若某項做法有替代方案，請在這份文件補上「決策紀錄」，說明為何選 B 而不選 A。

## 交接規則

- 新的維護者或新的 AI / agent 接手時，請先閱讀：
  1. [AGENTS.md](AGENTS.md)
  2. [HANDOFF.md](HANDOFF.md)
- `AGENTS.md` 負責穩定規則與長期結構。
- `HANDOFF.md` 負責目前進度、外部狀態與決策脈絡，屬於動態交接檔，應隨工作進度持續更新。
- 若有「當初為什麼不選 A、而選 B」這類容易在模型切換時遺失的資訊，請優先寫進 `決策紀錄`。

## 目前狀態

- 主專案目前工作分支：`main`
- 主專案目前版本號：`1.4.1`
- 主專案目前已推到 `origin/main`
- 主專案目前工作區乾淨，`main` 與 `origin/main` 一致
- `menu.cmd` 已執行完成，`1.4.1` 產物已建立
- `1.4.1` 已完成一般使用者權限下的安裝 / 掃描 / 靜默安裝 / 靜默卸載驗證
- `v1.4.1` GitHub Release 已建立
- 舊的 winget `1.4.0` PR 已關閉

## 這一輪已完成

### 執行期路徑與權限修正

- 使用者資料改放 `%LOCALAPPDATA%\chkLink\data\`
  - `config.yaml`
  - `visited_link.yaml`
- `update.cmd` 改放安裝根目錄
- 不再主動建立安裝目錄下的 `data` 子目錄
- 舊版若把使用者資料留在安裝目錄，啟動時會嘗試搬移 / 複製到新位置
- 開發機原本殘留在 repo 根目錄 `data\` 的 `config.yaml` 與 `visited_link.yaml` 已移到 `%LOCALAPPDATA%\chkLink\data\`

### GUI 收尾流程修正

- 掃描完成收尾時，即使儲存 `visited_link.yaml` 失敗，也會先恢復按鈕狀態
- 失敗時會顯示警告訊息，而不是卡住在掃描中狀態

### 文件同步

- `README.md` 已改成：
  - 使用者資料路徑在 `%LOCALAPPDATA%\chkLink\data\`
  - `update.cmd` 在安裝根目錄
  - 開頭改為「一般使用者 / 維護者 / agent」三種文件入口
  - 補上 `HANDOFF.md` 為動態交接檔的定位說明
- `AGENTS.md` 已補充：
  - 使用者資料與程式持有檔案的分工
  - 目前工作進度應參考 `HANDOFF.md`
  - `HANDOFF.md` 是動態交接檔，應隨進度更新
- `doc\` 已新增：
  - `user-guide.md`：一般使用者操作手冊
  - `github-release-guide.md`：GitHub Release 教學
  - `winget-release-guide.md`：winget 發佈教學
- `user-guide.md` 已補充：
  - winget 安裝、查詢、升級、移除與適用情境說明
- `winget-release-guide.md` 已補充：
  - PR 合併後的索引刷新確認與使用者端安裝驗證步驟
- `github-release-guide.md` 已補充：
  - 已發佈 Release 可修改文案，但不要在同版號下替換不同產物

### winget 相關

- 主專案內已建立 `1.4.1` 的 winget 草稿：
  - `winget\PeterJu\chkLink\1.4.1\...`
- 本機 `winget-pkgs` fork 工作目錄已建立並推送新的 `1.4.1` 分支：
  - branch：`add-peterju-chklink-1.4.1`
  - commit：`db7fb6482`
- 已建立並送出新的 winget PR：
  - [PR #351979](https://github.com/microsoft/winget-pkgs/pull/351979)
- 新 PR 狀態：
  - 已於 2026-03-26 被合併到 `microsoft/winget-pkgs:master`
  - CLA 已完成
  - Validation / Publish pipeline 已通過
  - Reviewer 已核准
  - winget 索引已刷新，`winget search chkLink` / `winget show PeterJu.chkLink` 已可查到 `1.4.1`
- 舊的 `1.4.0` winget PR：
  - [PR #351447](https://github.com/microsoft/winget-pkgs/pull/351447)
  - 已留言說明將由 `1.4.1` 取代
  - 已關閉
- 已把 winget `PackageName` 定為 `chkLink`
- 已把 winget locale manifest 的 `Description` 調整為：

```text
chkLink 是一套 Windows 網站失效連結掃描工具，提供 GUI 與 CLI 兩種使用方式。
它會根據掃描層數遞迴掃描站內頁面、驗證內部連結的有效性、檢查圖片是否缺少 alt，並輸出 Excel 報告與 log 紀錄。
```

## 決策紀錄

### 1. 使用者資料改放 `%LOCALAPPDATA%`，不再寫回安裝目錄

- 選擇方案：
  - `config.yaml` 與 `visited_link.yaml` 改放 `%LOCALAPPDATA%\chkLink\data\`
- 未選方案：
  - 繼續放在安裝目錄
  - 要求使用者以系統管理員身份執行
  - 建議關閉 UAC / Smart App Control
- 原因：
  - 安裝在 `Program Files` 時，一般使用者對安裝目錄通常沒有寫入權限。
  - 先前已實際出現掃描完成後因收尾寫檔失敗，導致完成訊息與按鈕狀態無法正常恢復的現象。
  - 這是 Windows 桌面程式中典型的「user-owned data 應與 app-owned files 分離」問題。
  - 正確修法應是調整執行期路徑，而不是要求使用者提高權限。

### 2. `update.cmd` 放安裝根目錄，不放使用者目錄

- 選擇方案：
  - `update.cmd` 放在安裝根目錄
- 未選方案：
  - 跟著使用者資料一起放到 `%LOCALAPPDATA%`
  - 繼續放在安裝目錄下的 `data\update.cmd`
- 原因：
  - `update.cmd` 是程式持有的更新輔助檔，不是使用者資料。
  - 它跟 installer / 更新流程綁定，比較適合跟程式本體放在一起。
  - 改放安裝根目錄後，角色更清楚，也可取消安裝目錄下不必要的 `data` 子目錄。

### 3. 主專案版本升到 `1.4.1`，不回寫既有 `1.4.0`

- 選擇方案：
  - 將這次修正視為 `1.4.1`
- 未選方案：
  - 直接覆寫既有 `1.4.0` release / 發佈檔案（asset）
  - 讓 winget `1.4.0` PR 對應新的 installer
- 原因：
  - 這次不是單純文件修改，而是執行期路徑與實際行為修正。
  - 已發佈版本不應在同版本號下對應不同產物內容。
  - 以 `PATCH` 版號遞增最符合目前專案採用的 SemVer 精神。

### 4. winget `PackageName` 使用 `chkLink`

- 選擇方案：
  - `PackageName: chkLink`
- 未選方案：
  - `PackageName: 網頁失效連結掃描工具`
- 原因：
  - `chkLink` 與程式本體的 `APP_NAME`、installer 命名與 GitHub Release 檔名較一致。
  - 較短的產品名更適合 package catalog 識別。
  - 中文全名仍可放在 `Description` 內，不會失去說明性。

### 5. `1.4.0` 的 winget PR 不直接延用到修正版

- 選擇方案：
  - 保留目前 `1.4.0` PR 狀態，另外準備 `1.4.1`
- 未選方案：
  - 把已送審的 `1.4.0` 改成對應新 installer
- 原因：
  - `1.4.1` 已包含實際行為修正與執行期路徑調整，不應再回寫到舊版號。
  - 維持版本號與實際安裝檔內容一致，較符合 release 與 winget 提交邏輯。

## 這一輪主專案提交

- `c24abeb` `調整執行期資料路徑與更新輔助檔位置`
- `01dddef` `調整 winget 草稿描述內容`
- `0008af7` `將版本升級為 1.4.1`
- `98fd400` `補充交接規則與決策紀錄`
- `f6f5014` `調整 update.cmd 版控位置`
- `ecd058a` `更新交接狀態與 winget 進度`
- `9625b2b` `新增使用手冊並整理交接與發佈文件`

## 外部 repo 狀態

### winget-pkgs fork

- 本機 fork 工作目錄：`winget-pkgs`
- branch：`add-peterju-chklink-1.4.0`
- 最近一次提交：
  - `ad4ba4272` `Add PeterJu.chkLink version 1.4.0`
  - `e0e86fca9` `Refine PeterJu.chkLink locale description`
- 新分支：
  - `add-peterju-chklink-1.4.1`
- 新分支最近一次提交：
  - `db7fb6482` `Add PeterJu.chkLink version 1.4.1`

## 接下來要做

1. 補一次實機安裝驗證，確認使用者端能直接透過 `winget install PeterJu.chkLink` 安裝 `1.4.1`
2. 若你有對外公告管道，可補發一則「winget 已可安裝」的通知，避免使用者只看到 GitHub Release、不知道已上架 winget
3. 若後續再有流程或交接方式調整，持續同步更新 `README.md`、`AGENTS.md`、`HANDOFF.md`
4. 若進入下一輪功能或修正工作，再以新的進度覆寫這份交接狀態

## 目前不要做的事

- 先不要重寫既有 `1.4.0` release 發佈檔案（asset）

## 交接提醒

- 若後續進度有變，請優先更新這份 `HANDOFF.md`
- 若穩定規則或流程有變，再同步更新 `AGENTS.md` 與 `README.md`
