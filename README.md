# LLM PCFG Cracking Model

基於大型語言模型（LLM）與概率上下文無關文法（PCFG）的密碼破解模型。  
核心流程：先用 BPE Tokenizer 將密碼分割成有意義的子字串（token），再以此訓練 LLM 生成符合密碼分佈的候選密碼。

---

## 專案結構

```
├── config.yaml              # 全域設定檔
├── processData.py           # 密碼資料清洗與預處理
├── trainBPE.py              # BPE Tokenizer 訓練入口
├── src/
│   └── BPE.py               # BPE 模型建構（標準模式 + PwdSegment 模式）
├── util/
│   ├── data.py              # 資料載入、清洗、去重工具
│   ├── trainTokenizer.py    # Tokenizer 訓練分派器
│   └── cloud.py             # 詞彙頻率詞雲視覺化
├── datasets/                # 原始密碼資料集（每行一個密碼，gitignore）
├── models/                  # 訓練產物（gitignore）
└── gen/                     # 生成圖片輸出
```

---

## 執行流程

### Step 1：資料清洗
```bash
python processData.py
```
讀取 `datasets/` 下的原始密碼檔（`.txt`），依 `config.yaml` 的 `password_cleaning` 設定進行過濾與去重。  
輸出：`datasets/cleaned/<dataset>/`

### Step 2：訓練 BPE Tokenizer
```bash
python trainBPE.py
```
輸出至 `models/tokenizer/<dataset>/`：

| 檔案 | 說明 |
|---|---|
| `tokenizer.json` | HuggingFace 標準格式，含 vocab + merge rules，供模型使用 |
| `vocab_freq.json` | 所有 token 的出現頻率 |
| `vocab_with_freq.json` | 所有 token 含 id + 頻率，依頻率排序 |
| `merged_vocab.json` | 僅合併後的多字元 token（length ≥ 2），依頻率排序 |

### Step 3：詞雲視覺化
```bash
python util/cloud.py
```
讀取 `vocab_with_freq.json`，取前 `top_k` 個 token 生成詞雲。  
輸出：`gen/cloud/<dataset>.png`

---

## BPE 模式說明

本專案支援兩種 BPE 訓練模式，由 `config.yaml` 的 `avg_len` 欄位控制：

| 模式 | `avg_len` 設定 | 停止條件 | 用途 |
|---|---|---|---|
| 標準模式 | `null` | 達到 `vocab_size` | 一般用途 |
| PwdSegment 細粒度 | `1.8` | 詞彙平均長度 ≥ 1.8 | CKL_Backoff、CKL_FLA |
| PwdSegment 粗粒度 | `4.5` | 詞彙平均長度 ≥ 4.5 | CKL_PCFG |

PwdSegment 模式實作自 Ming Xu et al. CCS'21，以詞彙表平均 token 長度作為停止條件，使分割結果更符合密碼的語義結構。

---

## 主要設定（config.yaml）

```yaml
bpe:
  train: true
  vocab_size: 4096
  min_frequency: 2
  avg_len: 4.5              # null=標準模式；1.8=細粒度；4.5=粗粒度
  save_path: "models/tokenizer/000webhost"
  train_corpus: "datasets/cleaned/000webhost"

password_cleaning:
  data_path: "datasets"
  dataset: ['000webhost']
  min_length: 8
  max_length: 20
  allowed_charsets:
    lowercase: true
    uppercase: true
    digits: true
    special: true
  reject_non_ascii: true
  reject_all_same_char: true
  dedup: true
  output_path: "datasets/cleaned/000webhost"

cloud:
  data_path: "models/tokenizer/000webhost/vocab_with_freq.json"
  top_k: 3000
  output_path: "gen/cloud/000webhost.png"
```

---

## 詞雲範例

![詞雲](gen/cloud/000webhost.png)

---

## 參考文獻

- Ming Xu et al., *Password Cracking with PwdSegment*, ACM CCS 2021
