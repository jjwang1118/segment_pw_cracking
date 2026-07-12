# 參數報告：Mistral-7B-v0.1 run_10（訓練 + 評估）

來源：[results/train/job-258508.out](../../results/train/job-258508.out)、[results/eval/eval-258985.out](../../results/eval/eval-258985.out)
（訓練超參數另交叉比對 `checkpoints/Mistral-7B-v0.1/run_10/lora_final/adapter_config.json` 與 `checkpoint-650/training_args.bin`，數值一致）

## 一、訓練參數（job-258508）

| 項目 | 值 |
|---|---|
| 基底模型 | `models/Mistral-7B-v0.1` |
| LoRA 模式 | `lora`（標準 bf16 LoRA，**非** QLoRA／未做 4-bit 量化） |
| 訓練資料 | `datasets/processed/semanticPCFG/COMB/backoff/split/train_data.jsonl`（262,263 筆） |
| 驗證資料 | 同目錄 `test_data.jsonl`（13,513 筆） |
| Prompt Template ID | 5（inline `<tag>` placeholder，訓練/推論 prompt 相同） |
| 輸出目錄 | `checkpoints/Mistral-7B-v0.1/run_10` |

### Trainer 超參數

| 參數 | 值 |
|---|---|
| per_device_train_batch_size | 64 |
| gradient_accumulation_steps | 64（有效 batch = 4096） |
| per_device_eval_batch_size | 32 |
| num_train_epochs | 10 |
| total_steps / max_steps | 640（log 開頭列印）／650（trainer_state 實際 global_step） |
| warmup_steps | 64 |
| learning_rate | 2e-4 |
| lr_scheduler_type | linear |
| weight_decay | 0.01 |
| optim | adamw_torch |
| adam_beta1 / beta2 / epsilon | 0.9 / 0.999 / 1e-8 |
| max_grad_norm | 1.0 |
| label_smoothing_factor | 0 |
| bf16 / fp16 | true / false |
| gradient_checkpointing | true |
| seed / data_seed | 42 |
| eval_strategy / eval_steps | steps / 20 |
| save_strategy / save_steps | steps / 20 |
| logging_steps | 10 |

### LoRA 設定（adapter_config.json）

| 參數 | 值 |
|---|---|
| r | 16 |
| lora_alpha | 32 |
| lora_dropout | 0.2 |
| target_modules | `q_proj`, `k_proj`, `v_proj` |
| bias | none |
| init_lora_weights | true |
| task_type | CAUSAL_LM |

### 訓練結果（log 尾端）

| 指標 | 值 |
|---|---|
| 最終 train_loss | 1.74 |
| 最終 eval_loss（epoch 10） | 1.649 |
| train_runtime | 3.043e4 秒（約 8.45 小時） |
| train_samples_per_second | 86.18 |

---

## 二、評估參數（eval-258985）

| 項目 | 值 |
|---|---|
| 基底模型 | `models/Mistral-7B-v0.1`（device=cuda, dtype=torch.float16） |
| LoRA adapter | `checkpoints/Mistral-7B-v0.1/run_10/lora_final` |
| 評估筆數 | 5,000 |
| 推論 Prompt Template ID | 5 |
| Max guess number | 1,000 |
| 測試集 | `datasets/processed/semanticPCFG/COMB/backoff/split/test_data.jsonl` |
| 輸出檔 | `gen/eval_results_id5_run_10_Mistral7B_id5_COMB.jsonl` |

### 搜尋法設定（`config/search.yaml`）

| 項目 | 值 |
|---|---|
| search_type（主） | `constrained_beam_search` |
| beam_width | 1000（單一 int，每步上限依字元類別大小自動計算） |
| search_width | 1000 |
| batch_size | 1000 |
| precision | half |
| fallback_to_dynamic | true（tags 含 pos/pos_semantic 時，退回 `dynamic_beam_search`） |
| 退回法 beam_width | `[95, 1000×15]`（16 層） |
| 退回法 batch_size | 1000 |
| 退回法 eos_threshold | 0.001 |
| 退回法 min_len | 7 |

### Crack Rate（結果，附帶參考）

| @K | Cracked | Rate |
|---|---|---|
| @1 | 155 / 5,000 | 3.10% |
| @10 | 360 / 5,000 | 7.20% |
| @100 | 578 / 5,000 | 11.56% |
| @1000 | 851 / 5,000 | 17.02% |
