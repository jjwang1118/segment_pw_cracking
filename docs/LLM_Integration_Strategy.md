# LLM 對接策略：密碼生成模型設計方案

> 基於現有 BPE Tokenizer 訓練成果，探討如何將大語言模型（LLM）整合進密碼猜測 pipeline  
> 相關資源：`models/tokenizer/`、`datasets/cleaned/`

---

## 概覽

完成 BPE Tokenizer 訓練後，下一步是利用密碼語料訓練或微調語言模型，使其學習密碼的條件機率分佈，進而生成高命中率的候選密碼。本文件描述兩條可行路線：

| 方案 | 方法 | 優點 | 適用場景 |
|------|------|------|----------|
| 方案一 | Fine-tune 小型 LLM | 快速驗證、有預訓練基礎 | Baseline 建立、資源有限時 |
| 方案二 | 從頭訓練密碼專用 LM | 與自訓練 BPE 完全對齊 | 深度 domain-specific 研究 |
| 方案三 | PCFG + LLM 混合 | 結構可控、可解釋 | 進階生成、命中率最大化 |

---

## 方案一：Fine-tune 小型 LLM

### 核心概念

保留既有開源小型 LLM（如 GPT-2、LLaMA-3.2-1B）的原始 tokenizer，直接在密碼語料上進行 **Causal Language Model（CLM）fine-tune**。模型學習在給定前綴的條件下預測下一個 token，等同於學習密碼的字元條件機率：

$$P(\text{password}) = \prod_{t=1}^{T} P(c_t \mid c_1, c_2, \ldots, c_{t-1})$$

### 訓練資料格式

每個密碼包裝成序列，以特殊 token 標記邊界（`<bos>` 開頭、`<eos>` 結尾），字元間以空格分隔以利逐字元 tokenize。

> **注意**：原始 LLM tokenizer 對密碼字元不友善，通常每個字元各成一個 token，序列較長。這是方案一相對方案二的主要劣勢。

### 建議模型選擇

| 模型 | 參數量 | 備註 |
|------|--------|------|
| GPT-2 (small) | 117M | 最易取得，適合快速實驗 |
| GPT-2 (medium) | 345M | 表現較好，資源需求中等 |
| LLaMA-3.2-1B | 1B | 近年強力小模型，需申請授權 |

### 評估指標

- **Hit Rate**：生成密碼命中測試集的比例
- **Perplexity (PPL)**：模型對測試集密碼的困惑度
- **Token Overlap**：生成密碼的 BPE token 與測試集分佈的相似度

---

## 方案二：從頭訓練密碼專用 LM

### 核心概念

不依賴任何預訓練 LLM，改以自訓練的 BPE tokenizer 作為 vocabulary，從零初始化一個 Transformer 語言模型並完全在密碼語料上訓練。這是對方案一的直接延伸，也是與現有 BPE pipeline 整合最自然的方式。

模型同樣學習 Causal LM 目標：

$$P(\text{password}) = \prod_{t=1}^{T} P(\text{tok}_t \mid \text{tok}_1, \ldots, \text{tok}_{t-1})$$

但這裡的 $\text{tok}$ 是 BPE token（如 `pass`、`123`、`!@#`），而非逐字元，序列長度更短、語意更豐富。

### 與方案一的關鍵差異

| 面向 | 方案一 | 方案二 |
|------|--------|--------|
| Tokenizer | 原始 LLM tokenizer（字元導向） | 自訓練 BPE（密碼導向） |
| 模型初始化 | 預訓練權重（有通用語言知識） | 隨機初始化（純密碼知識） |
| 序列長度 | 長（逐字元） | 短（BPE token） |
| 訓練成本 | 低（只需 fine-tune） | 高（需從頭訓練） |
| 與 BPE 整合 | 間接 | 直接 |

### 模型架構選擇

建議使用 GPT-2 架構但縮小規模，因密碼語料遠小於自然語言語料：

| 配置 | 層數 | Hidden size | Heads | 參數量 | 備註 |
|------|------|-------------|-------|--------|------|
| Tiny | 4 | 128 | 4 | ~1M | 快速實驗 |
| Small | 6 | 256 | 8 | ~10M | 推薦起點 |
| Medium | 12 | 512 | 8 | ~85M | 資源充足時 |

vocab size 直接對應各資料集訓練出的 BPE vocab 大小（約 3,500–4,100）。

### 優勢

- **Token 效率高**：BPE 將 `password123!` 切成 `[pass][word][123][!]` 共 4 個 token，方案一逐字元需 12 個 token，注意力機制負擔更小
- **Domain 對齊**：vocab 完全來自密碼分佈，不含無關的自然語言 token
- **可控性**：vocab size、merge 次數皆可調，與上游 BPE 訓練參數一致
- **跨資料集研究**：可分別用 000webhost / hotmail / phpbb 各自訓練，研究不同密碼文化下的生成差異

### 潛在限制

- 訓練資料量相對 LLM 預訓練語料極小，模型容易 overfit，需搭配 dropout、early stopping
- 缺乏預訓練知識，對罕見密碼模式泛化能力不如方案一
- vocab 與其他資料集不相容，跨資料集 transfer 需重新訓練

### 評估指標

- **Hit Rate**：生成密碼命中保留測試集的比例（主要指標）
- **Perplexity（PPL）**：測試集密碼的困惑度，越低越好
- **Type-Token Ratio**：生成密碼的多樣性，避免模型退化為高頻密碼重複生成
- **BPE Token 分佈相似度**：生成密碼的 token 頻率分佈與訓練集的 KL divergence

---

## 方案三：PCFG + LLM 混合架構

### 核心概念

傳統 PCFG（Probabilistic Context-Free Grammar）密碼破解方法（如 Weir et al., 2009）將密碼拆解為結構模板（pattern），再統計各 segment 的填充機率。本方案以 LLM 取代其中的 segment 生成步驟，提升填充詞彙的語意豐富度。

**傳統 PCFG 流程**：密碼 `password123!` 被拆解為 pattern `[L8][D3][S1]`，各 segment 依靠頻率表 lookup 填充（如 `password`、`iloveyou`）。

**PCFG + LLM 流程**：pattern 結構不變，但 Letter segment 改由 LLM 依上下文生成，候選詞更豐富多元。

### 架構示意

密碼語料經 BPE Tokenizer 分割後，進入 PCFG 分析層抽取 pattern（如 `[word][digit][symbol]`）。各 segment 類型分別由對應子模型生成候選，最終組合成完整密碼候選列表：

- **Word segment**：LLM 生成
- **Digit segment**：統計頻率表或 LM 生成
- **Symbol segment**：統計頻率表或 LM 生成

### PCFG 分析層：Pattern 提取

利用 BPE Tokenizer 將密碼分割後，依 token 內容類型標記各 segment：

- **L**（Letter）：純字母 token，如 `pass`、`word` → `L4`
- **D**（Digit）：純數字 token，如 `123` → `D3`
- **S**（Symbol）：純符號 token，如 `!` → `S1`
- **M**（Mixed）：混合類型 token → `M{長度}`

例如 `password123!` 經 BPE 分割為 `[pass][word][123][!]`，對應 pattern 為 `L4L4D3S1`。

### Pattern 統計

對訓練集所有密碼提取 pattern 後統計頻率，找出 Top-N 高頻 pattern（如 `L6D2`、`L4D4`、`L8`），作為生成階段的採樣依據。

### LLM Segment 生成與密碼組合

針對每個 pattern，依序對各 segment 類型生成候選詞，再依照 pattern 的 segment 順序拼接成完整密碼候選。Letter segment 由 fine-tuned LM 生成；Digit / Symbol segment 優先使用統計頻率表，可視需求替換為 LM 生成。

### 訓練策略

| 子模型 | 訓練資料 | 備註 |
|--------|----------|------|
| Pattern LM | 所有密碼的 pattern 序列 | 學習 pattern 的機率分佈 |
| Word segment LM | 所有 Letter segment | 學習常見字母組合 |
| Digit segment | 統計頻率表（不需 LLM） | 如 `123`、`2024`、`00` |
| Symbol segment | 統計頻率表（不需 LLM） | 如 `!`、`!@#`、`!!` |

> **優化方向**：Word segment LM 可用 fine-tuned GPT-2 或直接查詢頻率表，先以頻率表作為 baseline，再比較引入 LLM 後命中率的提升。

### 評估

- 對每個 pattern 分別計算 Hit Rate，找出哪類 pattern 命中率最高
- 比較純 PCFG（頻率表填充）vs. PCFG+LLM 的命中率差異
- 控制生成密碼總數，確保比較公平

---

## 三方案比較

| 面向 | 方案一（Fine-tune LLM） | 方案二（從頭訓練） | 方案三（PCFG + LLM） |
|------|------------------------|-------------------|----------------------|
| 實作難度 | 低 | 中 | 高 |
| 訓練資源 | 低（fine-tune） | 中（從頭訓練） | 中（多個子模型） |
| 可解釋性 | 低（黑盒） | 低（黑盒） | 高（pattern 可視） |
| 命中率潛力 | 中高 | 高 | 高（結構導向） |
| 與 BPE 整合 | 間接 | 直接 | 直接（BPE 作為 segmenter） |
| 訓練資料需求 | 低（預訓練已有知識） | 高（需足夠密碼量） | 中 |
| 適合作為 | Baseline | Domain-specific 研究 | 最終系統 |

---

## 建議實驗流程

1. **方案一**：fine-tune GPT-2，建立 baseline hit rate
2. **方案二**：從頭訓練 BPE-based LM，比較與方案一的 hit rate 差異，量化自訓練 tokenizer 的實際價值
3. 用現有 BPE tokenizer 對訓練集做 pattern 統計，找出 Top-10 pattern
4. **方案三初步**：實作組合生成，先以頻率表填充各 segment，比較純 PCFG 與方案一/二
5. **方案三進階**：以 LLM 取代 Word segment 生成，比較 PCFG+LLM vs. 純 PCFG
6. **跨資料集評估**：在 phpbb 訓練，對 000webhost 測試，驗證各方案的泛化能力

---

## 參考資料

- Weir, M. et al. (2009). *Password Cracking Using Probabilistic Context-Free Grammars*. IEEE S&P.
- Radford, A. et al. (2019). *Language Models are Unsupervised Multitask Learners*. (GPT-2)
- Xu, M. et al. (2021). *Chunk-Level Password Guessing*. CCS '21. (`docs/BPE_in_PwdSegment.md`)
- PassGPT: Rando, J. et al. (2023). *PassGPT: Password Modeling and (Guided) Generation with LLMs*. arXiv:2306.01545.
