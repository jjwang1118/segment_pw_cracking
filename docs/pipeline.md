# 資料處理 & 訓練流程

## 快速索引

| 階段 | 指令 | 輸入 | 輸出 |
|------|------|------|------|
| 1. 清洗 | `python processData.py` | `datasets/*.txt` | `datasets/cleaned/*/cleaned_data.txt` |
| 2. BPE 訓練 | `python trainBPE.py` | cleaned_data.txt | `models/tokenizer/*/tokenizer.json` |
| 3. PCFG 標注 | `python run_tokenize.py` | cleaned_data.txt + tokenizer | `gen/tagged/*_tagged.csv` |
| 4. 切分資料集 | `python util/Dataprocess.py` | tagged CSVs | `datasets/processed/split/*.jsonl` |
| 5. 訓練 | `python run_train.py` | JSONL + Llama model | `checkpoints/*/lora_final/` |

---

## 完整流程圖

```
datasets/
  000webhost.txt  ──┐
  hotmail.txt     ──┼──► [1 清洗] ──► datasets/cleaned/{ds}/cleaned_data.txt
  phpbb.txt       ──┘         │
                              │
                              ├──► [2 BPE訓練] ──► models/tokenizer/{ds}/tokenizer.json
                              │
                              └──► [3 PCFG標注] ◄── tokenizer.json
                                        │
                                        ▼
                              gen/tagged/{ds}_{kind}_tagged.csv
                                  [Password, Tokens, Tags]
                                        │
                                   [4 切分] 
                                        │
                              datasets/processed/split/
                                  train_data.jsonl
                                  test_data.jsonl
                                        │
                                   [5 訓練]
                                        │
                              checkpoints/Llama-3.2-3B-Instruct/lora_final/
```

---

## 階段 1 — 原始資料清洗

**指令：** `python processData.py`  
**設定：** `config/config.yaml` → `password_cleaning`

### 做什麼

1. 讀取 `datasets/{name}.txt`（每行一個密碼）
2. 長度過濾：保留 `min_length ≤ len ≤ max_length`（預設 8–20）
3. 字元集過濾：依照 `lowercase / uppercase / digits / special` 旗標組成正則，去除不合規密碼
4. 去重（`drop_duplicates`）
5. 寫出至 `datasets/cleaned/{dataset}/cleaned_data.txt`（無標頭單欄 CSV）

### 關鍵設定

```yaml
# config/config.yaml
password_cleaning:
  dataset: [000webhost]     # 要處理的資料集名稱
  min_length: 8
  max_length: 20
  lowercase: true
  uppercase: true
  digits: true
  special: true
```

---

## 階段 2 — BPE Tokenizer 訓練

**指令：** `python trainBPE.py`  
**設定：** `config/config.yaml` → `bpe`

### 兩種訓練模式

| 模式 | 觸發條件 | 說明 |
|------|----------|------|
| **PwdSegment 模式** | `avg_len` 有值（如 4.5） | 自訂 BPE 迴圈，停止條件為平均 token 長度 ≥ avg_len，偏向粗粒度分詞 |
| **標準 HF 模式** | `avg_len: null` | 使用 HuggingFace `BpeTrainer`，停止條件為 vocab_size |

### PwdSegment 迴圈邏輯（`src/BPE.py`）

```
初始：每個密碼 = 各字元的 tuple，e.g. ("p","a","s","s","1","2","3")
迴圈：
  1. 統計所有相鄰字元對的頻率（以密碼出現次數加權）
  2. 選出頻率最高的對（同分時字典序決定）
  3. 合併該對 → 更新所有密碼的表示
  4. 計算當前詞彙平均長度
  停止：平均長度 ≥ avg_len，或詞彙數 ≥ vocab_size
```

### 輸出檔案

```
models/tokenizer/{dataset}/
  tokenizer.json       ← HuggingFace Tokenizer 物件
  vocab_freq.json      ← {token: count}
  vocab_with_freq.json ← {token: {id, freq}}，依 freq 降序，含所有 token
  merged_vocab.json    ← 同上，只含合併後的多字元 token（len ≥ 2）
```

### 關鍵設定

```yaml
# config/config.yaml
bpe:
  train: true
  vocab_size: 4096
  avg_len: 4.5          # null → 標準模式；4.5 → PwdSegment 粗粒度
  min_frequency: 1
  train_corpus: datasets/cleaned/000webhost
  save_path: models/tokenizer/000webhost/non_filter_freq
```

---

## 階段 3 — PCFG 分詞 + 語義標注

**指令：** `python run_tokenize.py`  
**設定：** `config/tokenize_setting.yaml`

### 流程

```
密碼字串
  │
  ▼
BPE encode（tokenizer.json）
  → tokens: ["pass", "123"]
  │
  ▼
semantic-guesser（BackoffTagger + GrammarTagger）
  → POS tag: ["nn", "cd"]
  → PCFG tag: ["nn", "number3"]
  │
  ▼
gen/tagged/{ds}_{tagtype}_tagged.csv
  Password | Tokens      | Tags
  pass123  | pass|123    | nn|number3
```

### 三種標注方式（`tagging.tagtype`）

| tagtype | 說明 | 範例 |
|---------|------|------|
| `pos` | 純 CLAWS7 詞性標注 | `nn`, `vvd`, `np` |
| `backoff` | 回退到字元結構標注（無法辨識時） | `number3`, `char4`, `special1` |
| `pos_semantic` | WordNet 語義標注 | `s.love.v.01`, `nn_unk` |

### 關鍵設定

```yaml
# config/tokenize_setting.yaml
dataset: 000webhost
tagging:
  tagtype: backoff        # pos / backoff / pos_semantic
  semantic_guesser_path: models/semantic-guesser
```

---

## 階段 4 — 資料集切分

**指令：** `python util/Dataprocess.py`  
**設定：** `config/train_config.yaml` → `segment_tag_path`

### 流程

1. 依 `segment_tag_path.dataset` 列表讀取所有 tagged CSV，加上 `source` 欄位後合併
2. 再次過濾密碼長度 8–20
3. 依 `expected_ratio`（預設 1.0）取樣
4. 依 `split_ratio`（預設 0.2）隨機切分 train / test
5. 寫出 JSONL 與長度分布統計

### JSONL 格式（每行一筆）

```jsonc
{
  "Password": "pass123",
  "Tokens":   "pass|123",
  "Tags":     "nn|number3",
  "source":   "000webhost"
}
```

### 輸出

```
datasets/processed/split/
  train_data.jsonl         ← 訓練集
  test_data.jsonl          ← 測試集
  length_distribution.json ← 各長度的密碼數量統計
```

> **注意：** 若輸出檔案已存在，程式會直接跳過，不重新生成。如需重新生成，請手動刪除。

---

## 階段 5 — LLM 微調（LoRA）

**指令：** `python run_train.py`  
**設定：** `config/train_config.yaml`

### 訓練樣本結構

每筆訓練樣本的 `input_ids` 由三段組成：

```
[BOS] + tokenize(系統提示) + tokenize(知識 JSON) + char_encode(密碼) + [EOS]
│──────────────── labels = -100 ─────────────────│──── 計算 loss ────────────│
```

**系統提示（prompt_id=0）：**
```
As a targeted password guessing model, your task is to utilize the
provided account information to guess the password.
```

**知識 JSON 範例：**
```json
{
  "This password can be segmented and tag into the following part":
    [["pass", "nn"], ["123", "number3"]],
  "For each segment, each tag represents the following meaning": {
    "nn":      "CLAWS7 POS tag for singular noun",
    "number3": "A 3-digit number sequence"
  }
}
```

**密碼編碼：** 字元逐一對應到 LLM 的 token ID（透過 `get_alpa`），**不使用** BPE 切詞。

> Loss 只計算在密碼部分；提示與知識段落皆被 mask（label = -100）。

### LoRA 設定

```yaml
lora_config:
  r: 16
  lora_alpha: 32
  target_modules: [q_proj, k_proj, v_proj]
  lora_dropout: 0.2
  bias: none
```

僅訓練 Attention 的 Q/K/V 投影層，可訓練參數量約為全模型的 0.1–1%。

### 訓練超參數

```yaml
train_config:
  model_name: Llama-3.2-3B-Instruct
  model_path: models
  num_train_epochs: 3
  per_device_train_batch_size: 4
  gradient_accumulation_steps: 64   # 有效 batch size = 256
  learning_rate: 5e-4
  weight_decay: 0.01
  warmup_ratio: 0.1
  bf16: true
  eval_strategy: steps
  eval_steps: 100
  save_steps: 200
  optim: adamw_torch
```

### 輸出

```
checkpoints/Llama-3.2-3B-Instruct/
  checkpoint-200/         ← 訓練過程 checkpoint
  checkpoint-400/
  ...
  lora_final/             ← 最終 LoRA adapter 權重
logs/Llama-3.2-3B-Instruct/  ← TensorBoard 日誌
```

---

## 推論

訓練完成後使用 `util/search.py` 的 CLI 進行密碼猜測：

```bash
python util/search.py \
  --model_path checkpoints/Llama-3.2-3B-Instruct/lora_final \
  --beam_width 200 \
  --max_length 16 \
  --top_k 1000 \
  --output results/candidates.tsv
```

詳見 `util/search.py` 內的 `contrastive_search` 函式。

---

## 常見問題

| 問題 | 原因 | 解法 |
|------|------|------|
| `OSError: model not found` | `train_config.yaml` 的 `model_path` 打錯 | 確認為 `models`（複數） |
| 訓練 loss 不下降 | JSONL 欄位名稱大小寫錯誤 | `Password`（大寫 P），詳見 `util/pw_tokenize.py` |
| `run_tokenize.py` 失敗 | semantic-guesser 路徑錯誤 | 確認 `tokenize_setting.yaml` 的 `semantic_guesser_path` |
| `Dataprocess.py` 無輸出 | JSONL 已存在直接跳過 | 手動刪除 `datasets/processed/split/` 再重跑 |
