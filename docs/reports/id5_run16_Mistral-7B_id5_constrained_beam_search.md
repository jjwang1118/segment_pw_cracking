# 參數報告：Mistral-7B-v0.1 run_16（訓練中）

來源：[config/train_config.yaml](../../config/train_config.yaml)（現行版本，尚未 commit）、`checkpoints/Mistral-7B-v0.1/run_16/checkpoint-20/`（trainer_state.json + adapter_config.json，訓練已開始，最新進度 step 20/10,250）
> 本報告於 run_16 訓練**進行中**寫入（第一節訓練參數已可與 checkpoint-20 交叉驗證一致）；待訓練與評估完成後再補上第二節評估參數與結果，比照 [id5_run15_Mistral-7B_id5_constrained_beam_search.md](id5_run15_Mistral-7B_id5_constrained_beam_search.md) 格式。

## 一、訓練參數

| 項目 | 值 |
|---|---|
| 基底模型 | `models/Mistral-7B-v0.1` |
| LoRA 模式 | `lora`（標準 bf16 LoRA，**非** QLoRA／未做 4-bit 量化） |
| 訓練資料 | `datasets/processed/semanticPCFG/COMB/backoff/split/train_data.jsonl`（262,263 筆） |
| 驗證資料 | 同目錄 `test_data.jsonl`（13,513 筆） |
| Prompt Template ID | 5（inline `<tag>` placeholder，訓練/推論 prompt 相同） |
| 輸出目錄 | `checkpoints/Mistral-7B-v0.1/run_16` |

### Trainer 超參數

| 參數 | 值 |
|---|---|
| per_device_train_batch_size | 4 |
| gradient_accumulation_steps | 64（有效 batch = 256） |
| per_device_eval_batch_size | 32 |
| num_train_epochs | 10 |
| max_steps（trainer_state 實際） | 10,250 |
| warmup_ratio | 0.1 |
| learning_rate | 2e-4 |
| weight_decay | 0.01 |
| optim | adamw_torch |
| label_smoothing_factor | 0 |
| bf16 | true |
| seed / data_seed | 42 / 42 |
| eval_strategy / eval_steps | steps / 20 |
| save_steps | 20 |
| logging_steps | 10 |
| eval_delay | 1 |

### LoRA 設定（`train_config.yaml` → `train.lora_config`，已與 checkpoint-20/adapter_config.json 交叉驗證一致）

| 參數 | 值 |
|---|---|
| r | 32 |
| lora_alpha | 64 |
| lora_dropout | 0.2 |
| target_modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj` |
| bias | none |
| init_lora_weights | true |

### 目前訓練進度（checkpoint-20，最新）

| 指標 | 值 |
|---|---|
| global_step / max_steps | 20 / 10,250 |
| epoch | 0.0195 |
| train loss（step 20） | 4.1603 |
| eval_loss（step 20，首次評估） | 3.6861 |

## 二、與前兩次規劃／已完成訓練的差異

| 參數 | run_14 草稿（未執行） | run_15（已完成） | run_16（本次，現行 config） |
|---|---|---|---|
| prompt_template_id | 5 | 5 | 5 |
| per_device_train_batch_size | 4 | 64 | **4** |
| gradient_accumulation_steps | 64 | 64 | 64 |
| 有效 batch size | 256 | 4096 | **256（與 run_14 草稿相同）** |
| total_steps | 10,240（估算） | 640（trainer_state 實際 650） | **10,250（trainer_state 實際）** |
| learning_rate | 5e-4 | 5e-4 | **2e-4（改回 run_13 水準）** |
| LoRA r / alpha | 32 / 64 | 32 / 64 | 32 / 64 |
| LoRA target_modules | +o_proj, gate_proj | +o_proj, gate_proj | +o_proj, gate_proj |

> **說明：** run_16 的 `per_device_train_batch_size` 由 run_15 的 64 改回 4（有效 batch size 隨之由 4096 降至 256，梯度更新次數增加約 16 倍，total_steps 由 650 增至 10,250），同時 `learning_rate` 由 run_15 的 5e-4 調降回 2e-4。run_15 report（[id5_run15_Mistral-7B_id5_constrained_beam_search.md](id5_run15_Mistral-7B_id5_constrained_beam_search.md)）觀察到 eval_loss 全程上升、crack rate 較 run_10 下降，推測與 learning_rate 過高有關；本次同時調整 batch size 與 learning_rate 兩項，LoRA 容量（r/alpha/target_modules）維持與 run_15 相同，若 crack rate 有變化，較難單獨歸因於 batch size 或 learning_rate 其中一項。
