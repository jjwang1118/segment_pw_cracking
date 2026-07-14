# eval-260642.out 訓練與評估參數整理

整理日期：2026-07-14
來源：
- [eval-260642.out](../eval-260642.out)（評估執行 log）
- [result/COMB/eval_config.json](../result/COMB/eval_config.json)（本次評估實際使用的參數快照，eval time 2026-07-13 09:15:14）
- [checkpoints/mistral_7b_COMB/train_config.json](../checkpoints/mistral_7b_COMB/train_config.json)（對應模型 `checkpoints/mistral_7b_COMB/final` 的訓練參數快照，training 2026-07-11 11:43:18 ～ 19:03:36）

## 1. 任務總覽

| 項目 | 訓練 | 評估 |
|---|---|---|
| do_train / do_eval | true / false | false / true |
| seo 模式 | targeted | targeted |
| model / tokenizer | `/home/u4996812/llm_pcfg_cracking/models/Mistral-7B-v0.1` | 同左 |

## 2. 訓練參數（checkpoints/mistral_7b_COMB/train_config.json）

### 2.1 基本設定

| 參數 | 值 |
|---|---|
| base_model / tokenizer | `/home/u4996812/llm_pcfg_cracking/models/Mistral-7B-v0.1` |
| train_data_path | `data/COMB/TRAIN.json` |
| validation_path | （未設定） |
| prompt_template_id | 0 |
| precision | half |
| tokenizer_padding_side | right |

### 2.2 LoRA 設定

| 參數 | 值 |
|---|---|
| r | 16 |
| target_modules | q_proj, k_proj, v_proj |
| lora_alpha | 32 |
| lora_dropout | 0.2 |
| bias | none |
| init_lora_weights | true |
| use_rslora / use_dora | false / false |
| fan_in_fan_out | false |

### 2.3 訓練超參數

| 參數 | 值 |
|---|---|
| output_dir | `checkpoints/mistral_7b_COMB/` |
| per_device_train_batch_size | 4 |
| gradient_accumulation_steps | 64 |
| 有效 batch size | 4 × 64 = 256 |
| learning_rate | 5e-4 |
| lr_scheduler_type | linear |
| num_train_epochs | 3 |
| max_steps | -1 |
| warmup_ratio / warmup_steps | 0.1 |
| weight_decay | 0.01 |
| optim | adamw_torch |
| adam_beta1 / adam_beta2 / adam_epsilon | 0.9 / 0.999 / 1e-08 |
| max_grad_norm | 1.0 |
| label_smoothing_factor | 0 |
| bf16 / fp16 | true / false |
| gradient_checkpointing | false |
| seed / data_seed | 42 / 42 |
| logging_steps | 1 |
| save_steps | 200 |
| save_total_limit | 3 |
| eval_strategy | steps |
| eval_steps | 100 |
| eval_delay | 1 |
| per_device_eval_batch_size | 16 |
| dataloader_num_workers | 0 |
| train_sampling_strategy | random |

## 3. 評估參數（result/COMB/eval_config.json）

### 3.1 基本設定

| 參數 | 值 |
|---|---|
| base_model / tokenizer | `/home/u4996812/llm_pcfg_cracking/models/Mistral-7B-v0.1` |
| lora_path | `checkpoints/mistral_7b_COMB/final` |
| test_path | `data/COMB/TEST.json` |
| test_limit | 5000 |

### 3.2 搜尋設定 (eval config)

| 參數 | 值 |
|---|---|
| prompt_template_id | 0 |
| batch_size | 100 |
| beam_width_list | `[95, 1000, 1000, ..., 1000]`（第1步 beam=95，其餘15步皆為1000，共16步） |
| vocab_limit | true |
| eos_threshold | 0.001 |
| max_guess_number | 1000 |
| search_algorithm | dynamic_beam_search |
| contrastive_alpha | 0.6 |

### 3.3 猜測輸出設定 (guesser config)

| 參數 | 值 |
|---|---|
| result_path | `result/COMB` |
| log_interval | 1 |
| log_guess_number | [1, 10, 50, 100, 500, 1000] |

## 4. 評估結果（eval-260642.out）

| 指標 | 結果 |
|---|---|
| 測試樣本數 | 5000 |
| Crack @1 | 0 / 5000 (0.00%) |
| Crack @10 | 110 / 5000 (2.20%) |
| Crack @50 | 296 / 5000 (5.92%) |
| Crack @100 | 414 / 5000 (8.28%) |
| Crack @500 | 592 / 5000 (11.84%) |
| Crack @1000 | 650 / 5000 (13.00%) |
| 總耗時 | 約 8:10:41（5000 筆，平均 5.89 it/s 反推約 5.9 秒/筆） |

## 5. Prompt 格式（prompt_template_id = 0）

```
<bos>As a targeted password guessing model, your task is to utilize the provided account information to guess the password.[sibling_password_1]</s>[sibling_password_2]</s>...[sibling_password_n]</s>[password]<eos>
```

- 訓練時 labels 遮罩指令與 sibling password 段，僅對 `[password]` 計算 loss。
- 評估時輸入序列到 `...</s>` 為止（不含 `[password]`），由模型生成猜測。

### 範例（取自 data/COMB/TEST.json）

```json
{
  "Knowledge": { "Old password": ["killafly22"] },
  "password": "killafly12"
}
```

對應的訓練輸入序列：

```
<bos>As a targeted password guessing model, your task is to utilize the provided account information to guess the password.killafly22</s>killafly12<eos>
```

對應的評估輸入序列（模型從此處開始生成猜測）：

```
<bos>As a targeted password guessing model, your task is to utilize the provided account information to guess the password.killafly22</s>
```

## 6. 備註

- 評估用的 `lora_path`（`checkpoints/mistral_7b_COMB/final`）對應訓練的 `output_dir`（`checkpoints/mistral_7b_COMB/`），為同一組實驗的訓練與評估流程。
- `search_algorithm`（dynamic_beam_search）與 `contrastive_alpha`（0.6）未出現在 `config/evaluation_126_csdn_config.ini` 中，是程式執行時額外記錄於 `result/COMB/eval_config.json` 的參數（可能為程式內部預設值）。
- 目前 `config/training_126_csdn_config.ini` 的 `output_dir` 已改為 `checkpoints/mistral_7b_COMB_plainformat/`，與本次 eval-260642.out 所用的 `checkpoints/mistral_7b_COMB/` 不同，故訓練參數以 `checkpoints/mistral_7b_COMB/train_config.json` 快照為準，而非目前 ini 檔內容。
