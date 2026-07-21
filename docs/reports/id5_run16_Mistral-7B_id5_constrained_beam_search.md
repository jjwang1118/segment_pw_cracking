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

## 二、訓練狀況與 lora_final 來源

- `trainer_state.json` 顯示 eval_loss 在 step 2620 達最低點 1.6733,之後 step 2980→3020 由 1.7827 瞬間跳到 4.1620,自此發散、直到最後存檔的 checkpoint-3980（eval_loss ≈ 12.23）都未恢復
- 目前無對應訓練程序在跑（非本次 job 268989）,已停在 checkpoint-3980
- `lora_final` 由 `checkpoint-2620`（發散前最佳點）手動複製 `adapter_config.json` + `adapter_model.safetensors` + `README.md` 產生,而非訓練結尾的劣化權重

