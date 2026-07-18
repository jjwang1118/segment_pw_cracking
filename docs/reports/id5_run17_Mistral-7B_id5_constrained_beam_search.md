# 參數報告：Mistral-7B-v0.1 run_17（訓練，尚未執行）

來源：[config/train_config.yaml](../../config/train_config.yaml)（現行版本，尚未 commit）
> 本報告於 run_17 訓練**開始前**寫入，僅含訓練參數（第一節）；`checkpoints/Mistral-7B-v0.1/run_17` 目錄已存在但尚無 checkpoint。待訓練與評估完成後再補上第二節評估參數與結果，比照 [id5_run15_Mistral-7B_id5_constrained_beam_search.md](id5_run15_Mistral-7B_id5_constrained_beam_search.md) 格式。
>
> **本次規劃與 run_14 草稿（[id5_run14_Mistral-7B_params.md](id5_run14_Mistral-7B_params.md)，當時未執行）參數完全相同**：`per_device_train_batch_size=4`、`learning_rate=5e-4`，其餘設定不變。

## 一、訓練參數（規劃值，尚未執行）

| 項目 | 值 |
|---|---|
| 基底模型 | `models/Mistral-7B-v0.1` |
| LoRA 模式 | `lora`（標準 bf16 LoRA，**非** QLoRA／未做 4-bit 量化） |
| 訓練資料 | `datasets/processed/semanticPCFG/COMB/backoff/split/train_data.jsonl`（262,263 筆） |
| 驗證資料 | 同目錄 `test_data.jsonl`（13,513 筆） |
| Prompt Template ID | 5（inline `<tag>` placeholder，訓練/推論 prompt 相同） |
| 輸出目錄 | `checkpoints/Mistral-7B-v0.1/run_17` |

### Trainer 超參數

| 參數 | 值 |
|---|---|
| per_device_train_batch_size | 4 |
| gradient_accumulation_steps | 64（有效 batch = 256） |
| per_device_eval_batch_size | 32 |
| num_train_epochs | 10 |
| total_steps（估算） | 約 10,240（`262,263 // 256 ≈ 1,024`／epoch × 10） |
| warmup_ratio | 0.1 |
| learning_rate | 5e-4 |
| weight_decay | 0.01 |
| optim | adamw_torch |
| label_smoothing_factor | 0 |
| bf16 | true |
| seed / data_seed | 42 / 42 |
| eval_strategy / eval_steps | steps / 20 |
| save_steps | 20 |
| logging_steps | 10 |
| eval_delay | 1 |

### LoRA 設定（`train_config.yaml` → `train.lora_config`）

| 參數 | 值 |
|---|---|
| r | 32 |
| lora_alpha | 64 |
| lora_dropout | 0.2 |
| target_modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj` |
| bias | none |
| init_lora_weights | true |

## 二、與 run_14 草稿／run_15／run_16 的差異對照

| 參數 | run_14 草稿（未執行） | run_15（已完成） | run_16（進行中） | run_17（本次，現行 config） |
|---|---|---|---|---|
| prompt_template_id | 5 | 5 | 5 | 5 |
| per_device_train_batch_size | 4 | 64 | 4 | **4** |
| 有效 batch size | 256 | 4096 | 256 | **256** |
| total_steps | 10,240（估算） | 650（實際） | 10,250（實際） | **10,240（估算，未執行）** |
| learning_rate | 5e-4 | 5e-4 | 2e-4 | **5e-4（改回 run_14／run_15 水準）** |
| LoRA r / alpha | 32 / 64 | 32 / 64 | 32 / 64 | 32 / 64 |
| LoRA target_modules | +o_proj, gate_proj | +o_proj, gate_proj | +o_proj, gate_proj | +o_proj, gate_proj |

> **說明：** run_17 的參數組合與 run_14 草稿完全一致（batch size=4、learning_rate=5e-4），但 run_14 草稿當初從未實際執行訓練。run_16（batch=4、learning_rate=2e-4）目前訓練進行中（截至記錄時最新進度為 step 20/10,250）；run_17 是否等待 run_16 完成或另行啟動，須由使用者決定，避免兩者同時佔用 GPU 資源。LoRA 容量設定（r/alpha/target_modules）三次規劃均相同，因此 run_17 與 run_16 之間的差異單純化為 `learning_rate` 一項（2e-4 vs 5e-4）。
