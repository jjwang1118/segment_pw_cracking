# BPE Tokenizer 分析報告

> 分析對象：三個密碼資料集（000webhost、hotmail、phpbb）的 BPE Tokenizer 訓練結果  
> 使用檔案：各資料集 `models/tokenizer/{dataset}/` 下（`min_frequency > 1`，非 `non_filter_freq/`）  
> 分析腳本：`util/analyze.py`  
> 輸出路徑：`gen/analysis/`

---

## 1. 資料集基本資訊

| 資料集 | 詞彙表大小 | 最高頻 token 頻率 | 最低頻 token 頻率 |
|--------|-----------|-----------------|-----------------|
| 000webhost | 4,090 | 21,792 | 2 |
| hotmail    | 3,471 |    117 | 1 |
| phpbb      | 4,092 |  3,476 | 1 |

**觀察**：000webhost 詞彙量與 phpbb 接近，hotmail 則明顯較少。000webhost 的最高頻 token（`"1"`，freq=21,792）遠高於其他兩者，反映其語料規模較大。hotmail 頻率範圍極小（1–117），推測其 BPE 訓練語料量相對不足。

---

## 2. Zipf's Law 驗證

### 2.1 背景

Zipf's Law 指出自然語言中詞彙頻率與排名呈冪次關係：

$$f(r) \propto r^{-\alpha}$$

在 log-log 空間中，此關係應呈一條直線，斜率的絕對值即為 Zipf 指數 $\alpha$。自然語言通常 $\alpha \approx 1$；$\alpha < 1$ 表示頻率分佈較平坦（長尾較重），$\alpha > 1$ 則較陡峭（頭部 token 主導）。

### 2.2 符號說明

**α（Zipf 指數）— 描述「分佈形狀」**

$$f(r) \propto r^{-\alpha}$$

告訴你頻率隨排名下降的速度：

| 條件 | 意義 |
|------|------|
| $\alpha = 1$ | 標準 Zipf：第 2 名頻率 $= \frac{1}{2}$ 第 1 名，第 10 名 $= \frac{1}{10}$ 第 1 名 |
| $\alpha > 1$ | 衰減更快，頭部 token 更集中主導 |
| $\alpha < 1$ | 衰減較慢，長尾較重，分佈更平坦 |

**R²（決定係數）— 描述「符合程度」**

$$R^2 = 1 - \frac{SS_{res}}{SS_{tot}}$$

告訴你資料點有多貼合那條冪次曲線：

| 數值 | 意義 |
|------|------|
| $R^2 = 1.0$ | 完美符合冪次分佈 |
| $R^2 = 0.95$ | 95% 的變異可由冪次關係解釋，仍有少量偏差 |
| $R^2 \ll 1$ | 資料雜亂，不符合冪次分佈 |

> **兩者獨立**：α 定義曲線形狀（陡或緩），R² 衡量資料貼合該形狀的程度，可以獨立變化。

### 2.3 結果

| 資料集 | Zipf 指數 (α) | 決定係數 (R²) | 解讀 |
|--------|-------------|------------|------|
| 000webhost | **1.0534** | 0.9666 | 非常符合 Zipf's Law，頭部 token 稍微主導 |
| hotmail    | **0.8527** | 0.9522 | 分佈較平坦，頻率差距較小 |
| phpbb      | **1.0276** | 0.9748 | 最符合 Zipf's Law，R² 最高 |

> 圖表：[`gen/analysis/zipf/zipf_validation.png`](../gen/analysis/zipf/zipf_validation.png)  
> 統計 JSON：[`gen/analysis/zipf/zipf_stats.json`](../gen/analysis/zipf/zipf_stats.json)

### 2.4 討論

- **000webhost 與 phpbb**（α ≈ 1.03–1.05）符合自然語言的 Zipf 規律，說明密碼 BPE token 的使用模式與一般文字相近：少數高頻 token（如 `1`、`123`、`a`）佔據主要使用量，大量 token 只偶爾出現。
- **hotmail**（α = 0.853）偏低，頻率分佈更平緩。可能原因：
  1. 訓練語料量不足，高頻 token 無法大幅領先
  2. hotmail 用戶密碼組成更多樣化，缺乏明顯偏好模式
- 三個資料集的 R² 均超過 0.95，確認密碼 token 分佈整體遵循 Zipf's Law。

---

## 3. 低頻 Token Word Cloud

### 3.1 分析方法

- 資料來源：`merged_vocab.json`（BPE 合併後的 token，不含 base 字元如單一字母、數字）
- 取頻率最低的前 100 個 token，字體越大代表頻率越低
- hotmail 的 merged_vocab 中有部分 token freq=0（BPE 合併後無實際出現），以隨機權重呈現

### 3.2 各資料集低頻 Token 特徵

**000webhost**（freq 範圍：0–95）

低頻 token 出現較多**人名片段**與**網域相關字串**，如：
`-Nov`、`-Apr`、`chael`（Michael 的後綴）、`millah`、`rodri`（Rodriguez）、`muham`（Muhammad）、`@yahoo`、`@g`、`yahoo`、`windo`（windows）

→ 反映 000webhost 為網站帳號資料庫，密碼中夾雜真實名字與 email 相關字串，但這類組合屬於少數（低頻）。

**hotmail**（freq 全為 0）

所有底部 token 頻率皆為 0，代表 BPE 訓練時合併出這些 subword，但在語料中並未實際出現（或極為罕見）。這反映 hotmail 語料量不足，BPE 詞彙表中存在許多「過度合併」的 token。

**phpbb**（freq 範圍：1–14）

低頻 token 多為**英文名字片段**與**遊戲/社群用語**：
`micha`、`geor`（George）、`jord`（Jordan）、`thom`（Thomas）、`jose`、`adri`（Adrian）、`gogo`、`ragon`（dragon）、`ccer`（soccer）

→ phpbb 為論壇帳號資料庫，密碼中使用者名稱及暱稱相關字串更為常見，與遊戲、興趣相關的 subword 也有出現。

> 圖表目錄：[`gen/analysis/wordcloud/`](../gen/analysis/wordcloud/)

---

## 4. 跨資料集 Token 相似度比較

### 4.1 使用的 JSON 檔案

使用 **`vocab_freq.json`**，原因：
- 包含完整詞彙（base 字元 + BPE 合併結果），集合最完整
- 格式統一（`token → freq`），適合集合運算
- `merged_vocab.json` 僅含合併後 token，`vocab_with_freq.json` 資訊重複（多 id 欄位），均不如 `vocab_freq.json` 精簡全面

### 4.2 Pairwise Jaccard 相似度

$$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$

| 資料集對 | 交集大小 | 聯集大小 | Jaccard |
|---------|---------|---------|---------|
| 000webhost ↔ hotmail | 1,699 | 5,862 | **0.2898** |
| 000webhost ↔ phpbb   | 2,769 | 5,413 | **0.5115** |
| hotmail ↔ phpbb      | 1,539 | 6,024 | **0.2555** |

> 熱力圖：[`gen/analysis/cross_dataset/jaccard_heatmap.png`](../gen/analysis/cross_dataset/jaccard_heatmap.png)

**主要發現**：
- 000webhost 與 phpbb 相似度最高（0.51），說明兩者密碼構成模式接近，可能來源人群重疊（一般網路用戶）
- hotmail 與其他兩者相似度均偏低（~0.26–0.29），顯示 hotmail 用戶的密碼模式較為獨特；亦可能受語料量較小影響，導致低頻 BPE token 無法被訓練出來而降低交集

### 4.3 交集與非交集統計

| 類別 | Token 數 | 說明 |
|------|---------|------|
| **全三者交集（交集）** | **1,387** | 三個資料集均出現的 token |
| 恰好兩者共同 | 1,846 | 出現在任意兩個資料集中 |
| **000webhost 獨有（非交集）** | **1,009** | 僅出現在 000webhost |
| **hotmail 獨有（非交集）** | **1,620** | 僅出現在 hotmail |
| **phpbb 獨有（非交集）** | **1,171** | 僅出現在 phpbb |

> 統計圖：[`gen/analysis/cross_dataset/overlap_analysis.png`](../gen/analysis/cross_dataset/overlap_analysis.png)  
> 完整 JSON：[`gen/analysis/cross_dataset/cross_dataset_stats.json`](../gen/analysis/cross_dataset/cross_dataset_stats.json)

### 4.4 交集 Token 特徵

全三者共同的 1,387 個 token 範例（見 `cross_dataset_stats.json`）：

- **基礎數字序列**：`0`–`9`、`00`、`000`、`0000`、`01`、`02`、`12`、`123` 等
- **特殊符號**：`!`、`#`、`$`、`%`、`&`、`*`、`.`、`-`、`/`
- **常見網域字串**：`.com`
- **常見字母 bigram**：`an`、`er`、`in`、`al`、`as`、`ar`（高頻英文子字串）

→ 交集 token 主要為**基礎密碼組成元素**，在所有用戶群體中普遍使用。

### 4.5 各資料集獨有 Token 特徵

| 資料集 | 獨有 token 範例 | 推測原因 |
|--------|--------------|---------|
| **000webhost** | `000web`、`000webhost`、`.ru`、`-Apr-`、`-Sep-`、`010203` 等日期格式 | 網站名稱滲入密碼；東歐（.ru）用戶較多 |
| **hotmail** | `&1980`、`01022005`（完整日期）、`0123698745angel`、`.O`、`-Feb-`、`//54//` 等長字串 | 語料量不足導致過長合併；email 服務用戶有輸入完整生日等習慣 |
| **phpbb** | `0001`、`0815`、`0b`/`0c`/`0e`（十六進位前綴）、`1A`/`1C`（混合大小寫數字）、`ragon`（dragon）、`ccer`（soccer） | 論壇用戶偏好技術性與興趣主題密碼 |

---

## 5. 總結

| 面向 | 000webhost | hotmail | phpbb |
|------|-----------|---------|-------|
| 詞彙多樣性 | 高（4,090 tokens）| 中（3,471）| 高（4,092）|
| Zipf 符合程度 | 高（R²=0.97）| 中（R²=0.95）| 最高（R²=0.97）|
| 頻率範圍 | 寬（2–21,792）| 窄（1–117）| 中（1–3,476）|
| 與其他資料集相似度 | 與 phpbb 高（0.51）| 最低（0.26–0.29）| 與 000webhost 高（0.51）|
| 獨有 token 特色 | 網站名稱、地區性字串 | 長字串、完整日期 | 技術字串、興趣主題 |

**整體結論**：
1. 三個資料集均遵循 Zipf's Law（R² > 0.95），密碼 token 的使用模式具有自然語言特性
2. 000webhost 與 phpbb 同屬「一般網路用戶」族群，密碼模式相近；hotmail 偏差較大，可能與資料規模及用戶特性有關
3. 約 33.9%（1,387/4,092）的 token 為三資料集共用，構成密碼的通用詞彙核心；各資料集仍保有 25–47% 的獨有 token，反映不同平台用戶的密碼偏好差異
