# BPE 在密碼分割中的應用：PwdSegment 方法說明

> 論文來源：*Chunk-Level Password Guessing: Towards Modeling Refined Password Composition Representations*  
> Ming Xu et al., CCS '21, Fudan University

---

## 1. BPE 原始方法

**Byte-Pair Encoding（BPE）** 最初由 Philip Gage 於 1994 年提出作為資料壓縮技術，後被廣泛應用於 NLP 的 subword 分割（如 RoBERTa、GPT-2）。

### 核心流程

1. 在純文字語料庫上訓練
2. 將文字拆成字元序列
3. 反覆找出**最高頻的相鄰 token pair**，合併成一個新 token
4. 重複執行**指定次數**（作為 hyper-parameter）
5. 最終產生 subword 詞彙表

---

## 2. PwdSegment：密碼專用的 BPE 擴展

### 2.1 核心改動

原始 BPE 以「執行幾次 merge」作為停止條件，這個參數直覺上難以解釋且不易調整粒度。

PwdSegment 改為使用 **chunk 詞彙表的平均長度（`avg_len`）** 作為停止條件：

```
當 chunk 詞彙表的 avg_len >= 設定閾值 → 停止 merge
```

這樣做的好處：
- `avg_len` 比 merge 次數更能直觀描述詞彙表的粒度特性
- `avg_len` 較大 → 粒度較粗（coarse-grained）
- `avg_len` 較小 → 粒度較細（fine-grained）

---

## 3. PwdSegment 完整流程

### Step 1：Setup（初始化）

- 準備明文密碼訓練集
- 設定目標 `avg_len` 閾值

### Step 2：Input（輸入處理）

- 統計訓練集中每個密碼的出現頻率
- 將每個密碼拆成**字元序列**，並標記頻率

**範例：**

```
p @ s s w 0 r d 1 2 3 : 4   ← "p@ssw0rd123" 出現 4 次
p @ s s w 0 r d 4 e v e r : 3
l a s t 4 e v e r : 2
```

### Step 3：Merge Operation（迭代合併）

按照所有字元對的出現頻率由高到低反覆合併，每次合併最高頻的相鄰 pair：

```
Step-1: (w, 0) → w0   [出現 7 次，頻率最高]
  p @ s s w0 r d 1 2 3
  p @ s s w0 r d 4 e v e r
  l a s t 4 e v e r

Step-2: (w0, r) → w0r  [出現 7 次]
  p @ s s w0r d 1 2 3
  p @ s s w0r d 4 e v e r
  l a s t 4 e v e r

Step-3: (w0r, d) → w0rd
  ...（持續合併直到 avg_len 達到閾值）
```

> 若兩個 pair 頻率相同（如 `w 0` 和 `p @` 同為 7 次），依**字典序**決定優先合併哪一個。

每次 merge 後，詞彙表大小的變化有三種可能：

| 變化 | 說明 |
|------|------|
| **+1** | 新 chunk 加入，原始兩個 chunk 仍保留（兩者不總是一起出現） |
| **+0** | 新 chunk 加入，其中一個原始 chunk 被消除 |
| **-1** | 新 chunk 加入，兩個原始 chunk 都消除（兩者總是一起出現） |

### Step 4：Generate Chunk Vocabulary（停止並輸出）

停止條件（滿足任一即停）：
1. 詞彙表的 `avg_len >= 設定閾值`
2. 所有字元對的頻率都相同（無法繼續合併）

最終詞彙表由**單一字元**與**多字元 chunk** 混合組成。

**最終分割範例（avg_len = 4.5）：**

```
"p@ssw0rd4ever" → ["p@ssw0rd", "4ever"]
```

---

## 4. 在三個下游模型中的使用方式

不同模型對 `avg_len` 的需求不同，因此會訓練兩種粒度的詞彙表：

### 細粒度詞彙表（avg_len ≈ 1.8）→ 用於 CKL_Backoff、CKL_FLA

這兩個模型是 **context-relevant** 的（需要捕捉 chunk 之間的上下文關聯），較短的 chunk 能產生更多的組合，有助於建模密碼的序列依賴關係。

```
"p@ssw0rd4ever" → [p, @, s, sw, 0, r, d, 4, ever]
```

### 粗粒度詞彙表（avg_len ≈ 4.5）→ 用於 CKL_PCFG

CKL_PCFG 是 **context-independent** 的（不捕捉 chunk 間的順序關聯），較長的 chunk 能確保每個 chunk 內部具有完整的語義連貫性。

```
"p@ssw0rd4ever" → [p@ssw0rd, 4ever]
模板表示：TM8 DM5
```

---

## 5. 方法總結

```
原始 BPE
  ├── 停止條件：merge 次數（難以解釋）
  └── 應用場景：自然語言 subword 分割

PwdSegment（擴展）
  ├── 停止條件：avg_len 閾值（更直覺、可調粒度）
  ├── 訓練資料：明文密碼資料集（password-relevant）
  └── 輸出
        ├── avg_len ≈ 1.8（細粒度）→ CKL_Backoff、CKL_FLA
        └── avg_len ≈ 4.5（粗粒度）→ CKL_PCFG
```
