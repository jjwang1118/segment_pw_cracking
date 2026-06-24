# LLM PCFG Cracking Model

基於大型語言模型（LLM）與概率上下文無關文法（PCFG）的密碼破解模型。  
核心流程：將密碼切分為有意義的子字串（token），再透過 `semantic-guesser` 的 PCFG 對每個 token 貼上語義標籤，以此訓練 LLM 生成符合密碼分佈的候選密碼。

**切分方式（兩條路）：**
- **BPE（legacy）**：以字元頻率合併的 Byte-Pair Encoding，切出 `drag|on|99|!`（任意切）
- **PCFG-native（current）**：用 PCFG 自己的 regex + `wordsegment`，切出 `dragon|99|!`（依字元類別切）

PCFG-native 的切分結果與標籤語意一致，是目前主線方法。

---

## 專案結構

```
├── config/
│   ├── config.yaml              # BPE 訓練 + 資料清洗 + 詞雲設定
│   ├── tokenize_setting.yaml    # BPE Tokenize + PCFG 貼標籤設定（BPE path）
│   ├── pcfg_segment.yaml        # PCFG-native 切分 + 貼標籤設定（current）
│   ├── train_config.yaml        # LLM 訓練超參數 + LoRA 設定
│   └── search.yaml              # 搜索方法選擇 + 推論 + 評估設定
├── src/
│   ├── BPE.py                   # BPE 模型建構（標準模式 + PwdSegment 模式）
│   ├── Tokenize.py              # BPE 推論 + PCFG 貼標籤（BPE path）
│   ├── PCFGSegment.py           # PCFG-native 切分器（PCFGSegmenter class）
│   └── prompt_template.py       # LLM prompt 模板
├── util/
│   ├── data.py                  # 資料載入、清洗、去重工具
│   ├── trainTokenizer.py        # Tokenizer 訓練分派器
│   ├── cloud.py                 # 詞彙頻率詞雲視覺化
│   ├── Dataprocess.py           # JSONL 分割 + 長度分佈（BPE path）
│   ├── pw_tokenize.py           # 字元級編碼 + 訓練批次預處理
│   ├── train.py                 # LLM 訓練流程（載入模型、LoRA、Trainer）
│   ├── search.py                # 推論：dynamic_beam_search + contrastive_search
│   └── analyze.py               # Token 分析（Zipf 定律、跨資料集統計）
├── datasets/
│   ├── *.txt                    # 原始密碼資料集（每行一個密碼）
│   ├── cleaned/{dataset}/       # Stage 1 清洗後輸出
│   ├── processed/{tagtype}/split/               # BPE path JSONL
│   └── processed/semanticPCFG/{tagtype}/split/  # PCFG-native path JSONL
├── models/
│   ├── tokenizer/{dataset}/     # BPE tokenizer 輸出
│   ├── semantic-guesser/        # 外部 PCFG tagger（兩條 path 都需要）
│   └── Llama-3.2-3B-Instruct/  # 基礎 LLM 權重
├── checkpoints/                 # LoRA checkpoint 輸出
├── gen/
│   ├── tokenized/               # BPE tokenization CSV
│   ├── tagged/                  # BPE path 貼標籤 CSV（3 tagtype × 3 dataset）
│   └── semanticPCFG/            # PCFG-native path 貼標籤 CSV（3 tagtype × 3 dataset）
├── pcfg_tags.py                 # PCFG tag 定義 + get_explanation()
├── processData.py               # Stage 1：密碼清洗（兩條 path 共用）
├── trainBPE.py                  # Stage 2：BPE Tokenizer 訓練（BPE path only）
├── run_tokenize.py              # Stage 3：BPE 切分 + PCFG 貼標籤（BPE path）
├── run_pcfg_segment.py          # PCFG-native 切分 + 貼標籤 + 分割（current）
├── run_train.py                 # LLM 微調（兩條 path 共用）
├── run_search.py                # 密碼生成（無評估）
└── run_eval.py                  # 評估（crack rate）
```

---

## 執行流程

### Pipeline A — BPE 切分（legacy）

```
processData.py → trainBPE.py → run_tokenize.py → util/Dataprocess.py → run_train.py
```

### Pipeline B — PCFG-native 切分（current）

```
processData.py → run_pcfg_segment.py → run_train.py
```

Pipeline B 以單一腳本取代 Step 2–4，不需要 BPE tokenizer。

---

### Step 1：資料清洗（兩條 path 共用）
```bash
python processData.py
```
依 `config.yaml` 的 `password_cleaning` 設定過濾與去重。  
輸出：`datasets/cleaned/{dataset}/cleaned_data.txt`

---

### Step 2（Pipeline A）：訓練 BPE Tokenizer
```bash
python trainBPE.py
```
輸出至 `models/tokenizer/{dataset}/`：`tokenizer.json`、`vocab_freq.json`、`vocab_with_freq.json`、`merged_vocab.json`

---

### Step 3（Pipeline A）：BPE 切分 + PCFG 貼標籤
```bash
python run_tokenize.py
```
對每個密碼的 BPE token 貼上 PCFG 語義標籤。

輸出：
- `gen/tokenized/{dataset}_tokenized.csv`
- `gen/tagged/{dataset}_{tagtype}_tagged.csv`

**切分範例（BPE）：** `dragon99!` → `drag|on|99|!` → `char4|char2|number2|special1`

---

### Step 2+3（Pipeline B）：PCFG-native 切分 + 貼標籤 + 分割
```bash
# 全部 tagtype × 全部 dataset
python run_pcfg_segment.py

# 只跑單一 tagtype
python run_pcfg_segment.py --tagtype backoff

# CSV 已存在，只重做 train/test 分割
python run_pcfg_segment.py --split-only
```

分兩個 Stage：
- **Stage A**（打標）：讀 `datasets/cleaned/{dataset}/cleaned_data.txt` → PCFG 切分 + 貼標 → CSV
- **Stage B**（分割）：合併所有 dataset → 過濾長度 → 取樣 → train/test 分割 → JSONL

輸出：
- `gen/semanticPCFG/{dataset}_{tagtype}_tagged.csv`
- `datasets/processed/semanticPCFG/{tagtype}/split/train_data.jsonl`
- `datasets/processed/semanticPCFG/{tagtype}/split/test_data.jsonl`

**切分範例（PCFG-native）：** `dragon99!` → `dragon|99|!` → `nn|number2|special1`

---

### Step 4（Pipeline A only）：資料集分割
```bash
python util/Dataprocess.py
```
讀取 `gen/tagged/` 下所有 tagged CSV，依 `expected_ratio` 取樣、`split_ratio` 分割。  
輸出：`datasets/processed/{tagtype}/split/train_data.jsonl`、`test_data.jsonl`

> run_pcfg_segment.py 的 Stage B 取代原本 Dataprocess.py 做的事

---

### Step 5：LLM 微調（兩條 path 共用）
```bash
python run_train.py
```

修改 `config/train_config.yaml` 切換資料來源：

| 切分方式 | `dataset_path` | `segment_tag_path.path` |
|---|---|---|
| BPE path | `datasets/processed/backoff` | `gen/tagged` |
| PCFG-native path | `datasets/processed/semanticPCFG/backoff` | `gen/semanticPCFG` |

每筆訓練樣本包含 System prompt + Knowledge JSON（`{token: tag說明}`）+ 密碼（逐字元編碼），loss 只計算在密碼 token 上。  
輸出：`checkpoints/Llama-3.2-3B-Instruct/run_N/`

#### 從頭訓練
```bash
python run_train.py
```
自動建立新的 `run_N` 目錄（N 為目前最大編號 + 1）。

#### 從 checkpoint 繼續訓練
```bash
python run_train.py --resume checkpoints/Llama-3.2-3B-Instruct/run_4/checkpoint-800
```
沿用原 `run_4/` 目錄，Trainer 自動恢復 optimizer / scheduler 狀態並從 step 800 繼續。  
完成後 LoRA 最終權重存至 `run_4/lora_final`。

---

### Step 6：密碼生成
```bash
python run_search.py
```
不需要 ground-truth，直接生成候選密碼列表。  
輸出：`gen/{output_file_name}.jsonl`

---

### Step 7：評估（Crack Rate）
```bash
python run_eval.py
```
對 `test_data.jsonl` 中每筆密碼，以 Tokens + Tags 作為 prompt（不給模型看真實密碼），生成候選並計算 crack rate。  
輸出：`gen/eval_results.jsonl`，並列印 Crack Rate @ 1 / 10 / 100 / 1000。

---

## PCFG Tag 類型

| tagtype | 範例 tag | 說明 |
|---|---|---|
| `backoff` | `number2`, `char4`, `special1`, `mixed3` | 結構性字元類別（長度+類型） |
| `pos` | `nn`, `vv0`, `np`, `jj` | CLAWS7 詞性標籤 |
| `pos_semantic` | `s.love.v.01`, `nn_unk` | WordNet synset + 詞性組合 |
| 專有名詞 | `fname`, `mname`, `city`, `surname` | 命名實體類型 |

---

## 搜索方法

透過 `config/search.yaml` 的 `search_type` 欄位切換，`run_search.py` 與 `run_eval.py` 均支援：

| 方法 | `search_type` 值 | 說明 |
|---|---|---|
| **Contrastive Search** | `contrastive_search` | Beam Search + 對比懲罰（cosine similarity），避免重複生成 |
| **Dynamic Beam Search** | `dynamic_beam_search` | 純機率 Beam Search，無對比懲罰，適合 baseline 比較 |

```yaml
# config/search.yaml
search_type: dynamic_beam_search   # 改這一行即可切換
```

---

## 主要設定檔

### `config/pcfg_segment.yaml`（PCFG-native path）

```yaml
seed: 42
datasets: [000webhost, phpbb, hotmail]
tagtypes: [pos, backoff, pos_semantic]
semantic_guesser_path: models/semantic-guesser
dirs:
  datasets: datasets/cleaned
  tagged: gen/semanticPCFG
  processed: datasets/processed/semanticPCFG
password_filter:
  min_length: 8
  max_length: 20
expected_ratio: 0.4
split_ratio: 0.2
force_retag: false
```

### `config/train_config.yaml`（LLM 訓練）

```yaml
seed: 42
# BPE path:          dataset_path: datasets/processed/backoff
# PCFG-native path:  dataset_path: datasets/processed/semanticPCFG/backoff
dataset_path: datasets/processed/semanticPCFG/backoff
segment_tag_path:
  path: gen/semanticPCFG    # gen/tagged for BPE path
  kind: backoff             # pos | backoff | pos_semantic
  dataset: [hotmail, phpbb, 000webhost]
```

---

## 評估方法

評估的核心問題：**給定密碼的結構指紋（Tokens + Tags），模型能否在不知道真實密碼的情況下，將其列入候選清單中？**

### 兩種推論模式

| `prompt_template_id` | 模型收到的內容 | 用途 |
|---|---|---|
| `1` | 系統提示 + `{token字串: tag說明}` | 公平測試（與訓練格式一致）|
| `2` | 系統提示 + `{"password structure": "(tag1)(tag2)..."}` | 泛化測試（不給 token 字串）|

### 評估指標

| 指標 | 說明 |
|---|---|
| `min_cracked_guess_number` | 真實密碼在候選清單的排名；0 代表未破解 |
| **Crack rate @ K** | 在前 K 個候選內破解的密碼比例（K = 1, 10, 100, 1000）|

### 輸出格式（`gen/eval_results.jsonl`）

```json
{
  "index": 0,
  "real_password": "dragon99!",
  "tokens": "dragon|99|!",
  "tags": "nn|number2|special1",
  "source": "000webhost",
  "candidates": [["dragon99!", 0.91], ["dragon00!", 0.73]],
  "min_cracked_guess_number": 1
}
```

---

## 訓練紀錄

| Run | 切分方式 | Tag 類型 | Prompt | 備註 |
|---|---|---|---|---|
| run_1 | BPE | — | `id=0` | prompt 格式不一致，已廢棄 |
| run_5 → run_2 | BPE | `backoff` | `id=1` | 目前主線，訓練中 |
| run_3（planned）| PCFG-native | `pos` | `id=1` | 驗證 POS 標籤是否提升 crack rate |
| run_4（planned）| PCFG-native | `backoff` | `id=2` | 驗證高語意標籤效果 |

---

## 依賴套件

```bash
pip install torch transformers datasets peft tokenizers pandas numpy pyyaml wordcloud matplotlib
pip install wordsegment nltk
python -c "import nltk; nltk.download('wordnet')"
```

外部套件（需手動 clone）：
- `models/semantic-guesser/` — PCFG tagger，兩條 path 都需要
