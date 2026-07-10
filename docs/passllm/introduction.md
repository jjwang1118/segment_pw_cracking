# PassLLM Introduction

## Overview

PassLLM 是一個將大型語言模型（LLM）應用於密碼猜測的研究框架，支援兩種攻擊場景：

| 場景 | 說明 |
|------|------|
| **Trawling（撒網式）** | 不依賴目標資訊，大量生成高機率密碼，對未知帳號進行廣泛猜測 |
| **Targeted（針對性）** | 利用帳號附加資訊（如舊密碼）引導模型生成與目標相關的密碼 |

---

## 模型架構

### 基底模型
- **Mistral-7B-v0.1**：主力訓練模型（trawling / targeted fine-tuning）
- **Qwen2.5-0.5B-Instruct**：輕量學生模型（由 Mistral-7B 蒸餾而來）

### Fine-tuning 方式
- **LoRA**（Low-Rank Adaptation）：只訓練少量參數，凍結大部分基底模型權重
- 精度：bfloat16
- 詞表限制：95 個可列印 ASCII 字元，每個字元對應 tokenizer 中一個 token ID

```
95-char vocab = digits + lowercase + uppercase + special chars + space
```

### 知識蒸餾
- Teacher：Mistral-7B fine-tuned model
- Student：Qwen2.5-0.5B
- Loss：Forward KL Divergence（FKL），在密碼 token 位置對齊 teacher/student 的 logit 分佈

---

## 訓練流程

### Trawling 訓練
```
rockyou.txt（tab分隔）
    → process_train_trawling()    # 加 prompt prefix + 95-char encoding
    → LoRA fine-tuning
```

Prompt（template id=1）：
```
As a trawling password guessing model, your task is to generate user's passwords.
Password: <password_chars>
```

### Targeted 訓練
```
126_csdn_train.json
    → process_train_targeted()    # prompt + Knowledge(舊密碼) + 95-char encoding
    → LoRA fine-tuning（僅對密碼部分計算 loss）
```

Prompt（template id=0）：
```
As a targeted password guessing model, your task is to utilize the provided
account information to guess the password.
{"Old password": "shilpa"}<password_chars>
```

### Label Masking
訓練時 loss 只計算在密碼字元上（`mask_indice=True`、`mask_pii=True`），prompt 和帳號資訊部分的 label 設為 `-100`（忽略）。

---

## 搜索演算法

### 1. Dynamic Beam Search（DBS）— Targeted
針對性猜測的主要演算法，給定 prompt 後以 beam search 生成候選密碼。

- **Beam 寬度**可逐層變化（`beam_width_list`）
- 以累積 log-probability 排序候選
- 當某 beam 的 EOS 機率超過 `eos_threshold`，直接輸出該序列
- 使用 KV cache 共享 prompt 部分，避免重複計算

```
beam_width_list = [95, 1000] + [1000]*14   # 16 層
```

### 2. Contrastive Search — Targeted
在 DBS 基礎上加入對比懲罰，降低重複模式的候選分數，增加猜測多樣性。

- 每個 beam 累積歷史 hidden states
- 對新候選計算與歷史的最大 cosine similarity
- 調整分數：`(1 - α) × log_prob - α × max_similarity`
- `α`（`contrastive_alpha`）控制多樣性強度，預設 0.6

### 3. Width Search（BFS）— Trawling
以機率閾值為條件的廣度優先展開，生成所有累積機率高於 `threshold` 的密碼。

- 適合生成大規模字典（百萬級）
- 以 queue 管理待展開序列
- 超過 `max_length` 或機率低於 threshold 則剪枝

### 4. Divide Search（兩階段）— Trawling
大規模 trawling 的進階版本：

1. **Stage 1**：用 Priority Queue 取出前 `max_prefix` 個高機率 prefix
2. **Stage 2**：對每個 prefix 獨立執行 Width Search，結果合併輸出

---

## 評估流程

### Targeted 評估
```
126_csdn_test.json
    → process_test_targeted()     # 建構 prompt（不含密碼）
    → DBS / Contrastive Search    # 生成最多 max_guess_number 個候選
    → 比對 target password        # 記錄 min_cracked_guess_number
```

### 輸出檔案

| 檔案 | 說明 |
|------|------|
| `result_path/eval_config.json` | 評估時間 + 所有設定 |
| `result_path/input_output.jsonl` | 每筆：prompt、target、猜測列表（含機率）、crack rank |
| `result_path/log.txt` | 累計 crack rate（每 `log_interval` 筆更新） |

### 最終彙整（console + log.txt）
```
====================================================
 Evaluation Complete  |  Total: 500
====================================================
  Crack @1     :     12 / 500  (2.40%)
  Crack @10    :     48 / 500  (9.60%)
  Crack @100   :    110 / 500  (22.00%)
  Crack @1000  :    185 / 500  (37.00%)
====================================================
```

---

## 專案結構

```
models/passllm/
├── main.py                        # 主入口（train / eval / distill / wsgen / dsgen / csgen）
├── requirements.txt
├── config/
│   ├── training_rockyou_config.ini          # Trawling 訓練設定
│   ├── training_126_csdn_config.ini         # Targeted 訓練設定
│   ├── dis_config.ini                       # 蒸餾設定
│   ├── evaluation_126_csdn_config.ini       # DBS 評估設定
│   ├── evaluation_126_csdn_contrastive_config.ini  # Contrastive 評估設定
│   └── gendic_config.ini                    # Trawling 生成設定
├── src/
│   ├── model/
│   │   ├── train.py              # TPG_Trainer：LoRA fine-tuning
│   │   ├── eval.py               # GuessLLM_Evaluator：targeted 評估
│   │   ├── knowledge_distillation.py  # KGTrainer：FKL 蒸餾
│   │   └── data.py               # 資料載入工具
│   ├── search/
│   │   ├── search.py             # DBS / Contrastive / Width / Divide search 實作
│   │   ├── generation.py         # Trawling 生成的 config + runner 封裝
│   │   └── monto_carlo.py        # Monte Carlo 猜測數估計
│   └── utils/
│       ├── tokenize.py           # 95-char encoding、prompt 處理、label masking
│       ├── prompt_template.py    # Prompt template（id 0–4）
│       └── utils.py              # pm_guesser：結果儲存與 crack rate 計算
├── model/
│   ├── Mistral-7B-v0.1/
│   └── Qwen2.5-0.5B-Instruct/
├── checkpoints/
│   ├── 126_csdn_disQwen0.5B/    # Targeted 蒸餾 checkpoint
│   └── rockyou_100w_disQwen0.5B/ # Trawling 蒸餾 checkpoint
└── data/
    ├── rockyou/                  # Trawling 測試集
    └── 126_csdn/                 # Targeted 測試集
```

---

## 執行方式

```bash
cd models/passllm
python main.py --mode <mode> --config <config_file>
```

| Mode | 說明 | Config 範例 |
|------|------|------------|
| `train` | LoRA fine-tuning | `config/training_126_csdn_config.ini` |
| `eval` | Targeted 評估 | `config/evaluation_126_csdn_contrastive_config.ini` |
| `distill` | 知識蒸餾 | `config/dis_config.ini` |
| `wsgen` | Width Search 生成字典 | `config/gendic_config.ini` |
| `dsgen` | Divide Search 生成字典 | `config/gendic_config.ini` |
| `csgen` | Contrastive Search 生成字典 | `config/gendic_config.ini` |

> **注意**：所有路徑均以 `models/passllm/` 為工作目錄，須從該目錄執行。

---

## 與本專案的關係

PassLLM 作為獨立系統運行，與本專案（PCFG cracking model）的關聯僅在於：
- 使用相同來源的密碼資料集
- 可作為 baseline 或比較對象進行效能對比
