# Comparison Report: PassLLM vs 本研究 PCFG-LLM（COMB 資料集）

**資料集：** COMB（同一組 5,000 筆測試密碼，帳號取樣一致） · **基底模型：** 兩側皆為 Mistral-7B-v0.1 + LoRA

---

## 1. 訓練參數對照

| 項目 | 本研究 PCFG-LLM | PassLLM |
|---|---|---|
| 訓練資料 | `datasets/processed/semanticPCFG/COMB/backoff/split/train_data.jsonl`（PCFG-native 切分 + backoff tag） | `data/COMB/TRAIN.json`（原始 targeted json，含 old password） |
| prompt_template_id | 5 | 0 |
| LoRA 種類 | lora（標準 bf16） | lora（標準 bf16） |
| LoRA r / alpha | 16 / 32 | 16 / 32 |
| LoRA target_modules | q_proj, k_proj, v_proj | q_proj, k_proj, v_proj |
| LoRA dropout | 0.2 | 0.2 |
| per_device_train_batch_size | 64 | 4 |
| gradient_accumulation_steps | 64 | 64 |
| 有效 batch size | 4,096 | 256 |
| learning_rate | 2e-4 | 5e-4 |
| num_train_epochs | 10 | 3 |
| warmup_ratio | 0.1 | 0.1 |
| weight_decay | 0.01 | 0.01 |
| optim | adamw_torch | adamw_torch |
| bf16 | true | true |
| seed / data_seed | 42 / 42 | 42 / 42 |
| checkpoint | `checkpoints/Mistral-7B-v0.1/run_10/lora_final` | `checkpoints/mistral_7b_COMB/final` |

---

## 2. 評估參數對照

| 項目 | 本研究 PCFG-LLM | PassLLM |
|---|---|---|
| test_data | `datasets/processed/semanticPCFG/COMB/backoff/split/test_data.jsonl` | `data/COMB/TEST.json` |
| 測試筆數（去重後） | 5,000 | 5,000 |
| prompt_template_id | 5 | 0 |
| 搜尋法 | `constrained_beam_search`（backoff tag 全部時）／fallback `dynamic_beam_search`（含 pos/pos_semantic 時） | `dynamic_beam_search` |
| beam_width | 1,000（單一 int，per-step 上界依字元集自動限制） | `[95, 1000] × 15`（逐 step list） |
| batch_size | 1,000 | 100 |
| eos_threshold | （constrained 段：最後 step 強制 EOS） | 0.001 |
| max_guess_number | 1,000 | 1,000 |
| vocab_limit | true | true |
| precision | half | half |

---

## 3. 測試集筆數說明

兩側 `test_limit` 皆設為 5,000，且經比對，兩份測試集的帳號／密碼**完全相同**（5,000 筆唯一密碼，交集 = 5,000）。但 PassLLM 實際輸出的 `input_output.jsonl` 有 5,054 筆紀錄，其中 20 筆密碼各被重複評估 2–5 次（共 54 筆重複，重複紀錄的 `min_cracked_guess_number` 完全一致，屬於重跑/紀錄重複，非資料不一致）。為求公平比較，以下 crack rate 已對 PassLLM 結果依密碼去重（保留唯一 5,000 筆），本研究結果本身即為 5,000 筆、無需處理。

**雙方測試集一致性驗證：** 將本研究測試集的 5,000 筆密碼與 PassLLM 去重後的 5,000 筆密碼各自取集合比對——交集為 5,000 筆，「僅存在於本研究」與「僅存在於 PassLLM」皆為 0 筆。即兩側評估的是**完全相同的一組帳號密碼**，並非碰巧筆數相同而已，因此以下 crack rate 對照具備嚴謹的同測試集基礎。

---

## 4. Crack Rate 對照

| @K | 本研究 PCFG-LLM | PassLLM |
|---|---|---|
| @1 | 155 / 5,000（3.10%） | 0 / 5,000（0.00%） |
| @10 | 360 / 5,000（7.20%） | 425 / 5,000（8.50%） |
| @50 | 495 / 5,000（9.90%） | 765 / 5,000（15.30%） |
| @100 | 578 / 5,000（11.56%） | 914 / 5,000（18.28%） |
| @500 | 756 / 5,000（15.12%） | 1,020 / 5,000（20.40%） |
| @1000 | 851 / 5,000（17.02%） | 1,054 / 5,000（21.08%） |

## 5. 結果圖表

![Crack Rate Comparison](../../gen/results/comparison_PassLLM_vs_PCFG-LLM_COMB_result.png)
