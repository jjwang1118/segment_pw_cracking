# Git 操作參考

本專案常用的 git 操作速查。遠端為 `origin`（`git@github.com:jjwang1118/segment_pw_cracking.git`），主分支為 `main`。

---

## 1. 分支：建立、切換、起點

### 建立新分支並切換 — `git switch -c`
```bash
git switch -c <新分支名>            # 從「目前所在分支」長出新分支並切換
git switch -c <新分支名> <起點>     # 從指定「起點」長出新分支
```
- `-c` = `--create`（建立新分支）
- 第 1 個參數 = 要建立的**新**分支名（尚不存在）
- 第 2 個參數（起點，可省略）= 從哪個既有的點開始長

**起點可以是任何 commit 指得到的東西：**

| 起點類型 | 範例 | 意思 |
|---|---|---|
| 省略 | `git switch -c exp` | 從目前分支開 |
| 本地分支 | `git switch -c exp multi-structcand` | 從該分支開 |
| 遠端分支 | `git switch -c exp origin/main` | 從遠端 main 最新狀態開 |
| tag | `git switch -c exp v1.0` | 從 tag 開 |
| commit hash | `git switch -c exp 862041d` | 從該 commit 開 |

> 舊語法等價：`git checkout -b <新分支名> [起點]`

### 切換到已存在的分支
```bash
git switch <分支名>                # 舊語法：git checkout <分支名>
```

### 切到某個 commit 檢視（不建分支）— `git switch -d`
```bash
git switch -d <commit/tag/分支>    # = --detach，進入 detached HEAD
```
⚠️ detached HEAD 下的 commit **不屬於任何分支**，切走就可能遺失。要保留先 `git switch -c <新分支>`。

### `-c` vs `-d` 一句話
- **要開發** → `-c`（造新分支，commit 安全累積）
- **只想回頭看某個點** → `-d`（暫時脫離，看完就走）

---

## 2. 提交流程

```bash
git status -sb                     # 看目前狀態（分支 + 變更）
git add <檔案>                     # 暫存指定檔
git add -u                         # 暫存「已追蹤檔」的修改與刪除（不含新檔）
git add -A                         # 暫存全部（含新檔）
git diff                           # 看未暫存的變更
git diff --cached                  # 看已暫存（將提交）的變更
git commit -m "訊息"               # 提交
git commit -F msg.txt              # 用檔案內容當訊息（多行、含 trailer 方便）
```

> **本專案規則**：commit 訊息需經使用者確認，勿擅自決定；訊息結尾加
> `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。

### `git diff` 比較對象一覽
`git diff` 看的是「每一行具體怎麼改」（`git status` 只看哪些檔變了）。差別在於它比較哪兩個區域：

| 指令 | 比較對象 | 用途 |
|---|---|---|
| `git diff` | 工作區 vs 暫存區 | 看「還沒 add」的改動 |
| `git diff --cached` | 暫存區 vs HEAD | 看「已 add、將提交」的改動 |
| `git diff HEAD` | 工作區 vs 上一次 commit | 看「這次全部改動」（不管 add 沒） |
| `git diff <檔名>` | 只看某個檔 | `git diff run_eval.py` |
| `git diff main` | 工作區 vs main 分支 | 跟某分支比 |
| `git diff A B` | 兩個 commit/分支之間 | `git diff main..HEAD` |
| `git diff --stat` | 只看每檔增刪行數摘要 | 快速看規模，不看細節 |
| `git diff --name-only` | 只列變更檔名 | 只要清單 |

> 讀法：`-`（紅）= 刪除/改前，`+`（綠）= 新增/改後；`@@ -舊起,行數 +新起,行數 @@` 標示變更位置。按 `q` 離開分頁畫面。

---

## 3. 推送到 GitHub

### 首次推新分支（建立追蹤關係）
```bash
git push -u origin <分支名>        # -u = --set-upstream，只有首推需要
```
之後同一條分支再推，直接：
```bash
git push
```

### 其他變化
| 需求 | 指令 |
|---|---|
| 本地名 ≠ 遠端名 | `git push -u origin 本地名:遠端名` |
| 推之前先看會推什麼 | `git log origin/main..HEAD --oneline` |
| 刪除遠端分支 | `git push origin --delete <分支名>` |

---

## 4. 從乾淨 main 開新功能分支（建議流程）

```bash
git switch main && git pull        # 先把 main 更新到最新
git switch -c my-feature           # 開新分支（此時等同從最新 main 開）
# ... 改動 ...
git add -u && git commit -m "..."
git push -u origin my-feature      # 首推
```
或不切過去、直接從遠端 main 開：
```bash
git switch -c my-feature origin/main
```

---

## 5. 常用查詢

```bash
git branch --show-current                     # 目前分支名
git branch -vv                                # 本地分支 + 追蹤的遠端
git log --oneline -10                         # 最近 10 筆
git log origin/main..HEAD --oneline           # 本地領先遠端 main 的 commit
git status --porcelain                        # 機器可讀的狀態（空 = 乾淨）
git check-ignore -v <路徑>                    # 某路徑是否被 gitignore、被哪條規則
```

---

## 6. 撤銷 / 還原（小心使用）

用「三個區域」定位每個指令**動的是哪一區**：

```
工作區(working) ──add──▶ 暫存區(staged) ──commit──▶ 版本庫(HEAD/歷史)
```

### 速查表
| 需求 | 指令 | 動哪一區 | 你的改動 |
|---|---|---|---|
| 取消暫存（把 add 收回） | `git restore --staged <檔>` | 暫存區 | **保留** |
| 丟棄工作區未暫存改動 ⚠️ | `git restore <檔>` | 工作區 | **消失** |
| 從歷史某 commit 還原某檔 | `git checkout <commit> -- <路徑>` | 歷史→工作區 | 覆蓋該檔 |
| 改上一個 commit（未推送）合併成新commit | `git commit --amend` | 歷史 | 改寫上一筆 |
| 回退到某 commit（留改動） | `git reset <commit>`（mixed） | 歷史指標 | **保留於工作區** |
| **撤銷已推送的 commit** | `git revert <commit>` | 新增反向 commit | 安全、不改寫歷史 |

### `git restore` 兩種模式（差在 flag，不是「還原所有」）
路徑決定「範圍」（單檔 / `.` 全部），flag 決定「動哪一區」：
```bash
git restore --staged <檔>     # 取消 add：從暫存區退回未暫存，工作區改動保留
git restore <檔>              # 丟棄工作區未暫存改動 ⚠️ 不可逆
git restore --staged --worktree <檔>   # 兩者一起：完全丟棄一個「已 add」檔的改動
git restore .                 # 對「目前目錄以下全部」套用 ⚠️
```

### `git reset` 三種強度
```bash
git reset <commit>            # 預設 = --mixed
```
| 指令 | HEAD | 暫存區 | 工作區 |
|---|:---:|:---:|:---:|
| `--soft <c>` | 退回 | 保留(已暫存) | 保留 |
| `--mixed <c>`（預設） | 退回 | 清掉 | **保留** |
| `--hard <c>` | 退回 | 清掉 | **一併清掉 ⚠️ 不可逆** |

### ⚠️ 黃金守則：已推送的 commit 不要改寫歷史
`reset` / `--amend` 都會改寫 commit 歷史。若那些 commit **已 push 到遠端**，改寫後本地與遠端會分岔、拉取衝突。
**已推送要撤銷 → 用 `git revert <commit>`**：它不刪歷史，而是新增一個「反向 commit」抵銷該次改動，可安全 push。

---

## 本專案備註
- 大檔目錄 `checkpoints/`、`datasets/processed/`、`gen/`（部分）已被 `.gitignore` 排除，不會被推上去；資料靠腳本重建（如 `run_pcfg_segment.py`、`run_pcfg_combine_multistruct.py`）。
- eval 結果 jsonl 以 `gen/eval_results_all.zip`（LFS）封存，工作區的 `.jsonl` 可安全刪除後從 zip 還原。
