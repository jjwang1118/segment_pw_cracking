# 126_csdn 訓練與評估參數整理

整理日期：2026-07-12
來源：[config/training_126_csdn_config.ini](../config/training_126_csdn_config.ini)、[config/evaluation_126_csdn_config.ini](../config/evaluation_126_csdn_config.ini)

## 1. 任務總覽

| 項目 | 訓練 (training) | 評估 (evaluation) |
|---|---|---|
| do_train / do_eval | true / false | false / true |
| seo 模式 | targeted | targeted |

## 2. 訓練設定 (training_126_csdn_config.ini)

### 2.1 基本設定

| 參數 | 值 |
|---|---|
| model / tokenizer | `/home/u4996812/llm_pcfg_cracking/models/Mistral-7B-v0.1` |
| train_data | `data/COMB/TRAIN.json` |
| validation_data | （未設定） |
| prompt_template_id | 0 |
| precision | half |

### 2.2 LoRA 設定

| 參數 | 值 |
|---|---|
| r | 16 |
| target_modules | q_proj, k_proj, v_proj |
| lora_alpha | 32 |
| lora_dropout | 0.2 |
| bias | none |
| init_lora_weights | true |

### 2.3 訓練超參數

| 參數 | 值 |
|---|---|
| output_dir | `checkpoints/mistral_7b_COMB/` |
| per_device_train_batch_size | 4 |
| gradient_accumulation_steps | 64 |
| 有效 batch size | 4 × 64 = 256 |
| learning_rate | 5e-4 |
| num_train_epochs | 3 |
| warmup_ratio | 0.1 |
| weight_decay | 0.01 |
| optim | adamw_torch |
| label_smoothing_factor | 0 |
| bf16 | true |
| seed / data_seed | 42 / 42 |
| logging_steps | 1 |
| save_steps | 200 |
| evaluation_strategy | steps |
| eval_steps | 100 |
| per_device_eval_batch_size | 16 |
| eval_delay | 1 |

## 3. 評估設定 (evaluation_126_csdn_config.ini)

### 3.1 基本設定

| 參數 | 值 |
|---|---|
| base_model / tokenizer | `/home/u4996812/llm_pcfg_cracking/models/Mistral-7B-v0.1` |
| lora_path | `checkpoints/mistral_7b_COMB/final` |
| test_path | `data/COMB/TEST.json` |
| test_limit | 5000 |

### 3.2 搜尋設定 (search)

| 參數 | 值 |
|---|---|
| beam_width_list | `[95,1000] + [1000]*14`（第一步 beam=95/1000，之後 14 步皆為 1000） |
| batch_size | 100 |
| prompt_template_id | 0 |
| vocab_limit | true |
| precision | half |
| eos_threshold | 0.001 |
| max_guess_number | 1000 |

### 3.3 猜測輸出設定 (guesser)

| 參數 | 值 |
|---|---|
| result_path | `result/COMB` |
| log_interval | 1 |
| log_guess_number | [1, 10, 50, 100, 500, 1000] |

## 4. 備註

- 評估用的 `lora_path` (`checkpoints/mistral_7b_COMB/final`) 對應訓練的 `output_dir` (`checkpoints/mistral_7b_COMB/`)，兩者為同一組實驗的訓練與評估流程。
- 訓練與評估的 `prompt_template_id` 皆為 0，`precision` 皆為 half，設定一致。
