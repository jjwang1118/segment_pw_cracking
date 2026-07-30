# Eval Report: Mistral-7B-v0.1 · Template id=6 · constrained_beam_search（COMB dataset）

來源：[results/train/job-260943.out](../../results/train/job-260943.out)、[results/eval/eval-261839.out](../../results/eval/eval-261839.out)

> **注意：** 本報告原先不存在獨立檔案，run_13 的訓練/評估資料僅散見於 `param_compare.md`（§1.1）與
> `comparison_PassLLM_vs_PCFG-LLM_COMB.md`（§9.1）。此份為補齊的完整版本；Trainer 超參數表中
> 除 log 可直接驗證的欄位（total_steps/warmup_steps/global_step/loss/train_runtime 等）外，其餘
> 未在 log 開頭列印、且 run_13 未產生 `train_config_snapshot.json` 的欄位，依 `param_compare.md`
> 明確標註「固定：LoRA r=16/alpha=32/[q,k,v]、learning_rate=2e-4、10 epoch……其餘參數保持相同」，
> 沿用 run_10（同批次、同資料集，唯一差異為 prompt template id=5→6）之數值。

## 實驗設定

| 項目 | 值 |
|---|---|
| 模型 | Mistral-7B-v0.1 |
| LoRA | `checkpoints/Mistral-7B-v0.1/run_13/lora_final` |
| LoRA rank / alpha / target_modules | r=16, alpha=32, [q_proj, k_proj, v_proj] |
| 訓練 Template ID | 6（精簡純文字 prompt，對照組為 run_10 的 id=5） |
| 推論 Template ID | 6 |
| 評估筆數 | 5,000 |
| Max guess | 1,000 |
| 搜尋法（primary） | `constrained_beam_search` |
| 搜尋法（fallback） | `dynamic_beam_search`（當 tags 含 pos/pos_semantic 時） |
| 測試集 | `datasets/processed/semanticPCFG/COMB/backoff/split/test_data.jsonl`（同 run_10） |
| 來源 log | `results/eval/eval-261839.out` |

### Trainer 超參數（`results/train/job-260943.out`）

| 參數 | 值 | 來源 |
|---|---|---|
| 訓練資料 | `datasets/processed/semanticPCFG/COMB/backoff/split/train_data.jsonl`（262,263 筆） | log |
| 驗證資料 | 同目錄 `test_data.jsonl`（13,513 筆） | log |
| per_device_train_batch_size | 64 | 沿用 run_10 |
| gradient_accumulation_steps | 64（有效 batch = 4096） | 沿用 run_10 |
| per_device_eval_batch_size | 32 | 沿用 run_10 |
| num_train_epochs | 10 | log（`epoch: 10` 於結尾列印） |
| total_steps / max_steps | 640（log 開頭列印）／650（實際跑滿的 global_step） | log |
| warmup_steps | 64 | log |
| learning_rate | 2e-4 | 沿用 run_10 |
| lr_scheduler_type | linear | 沿用 run_10 |
| weight_decay | 0.01 | 沿用 run_10 |
| optim | adamw_torch | 沿用 run_10 |
| adam_beta1 / beta2 / epsilon | 0.9 / 0.999 / 1e-8 | 沿用 run_10 |
| max_grad_norm | 1.0 | 沿用 run_10 |
| bf16 / fp16 | true / false | 沿用 run_10 |
| gradient_checkpointing | true | 沿用 run_10 |
| seed / data_seed | 42 | 沿用 run_10 |
| eval_strategy / eval_steps | steps / 20 | 沿用 run_10 |
| save_strategy / save_steps | steps / 20 | 沿用 run_10 |
| logging_steps | 10 | 沿用 run_10 |

### LoRA 設定（`checkpoints/Mistral-7B-v0.1/run_13/lora_final/adapter_config.json`，實測值）

| 參數 | 值 |
|---|---|
| r | 16 |
| lora_alpha | 32 |
| lora_dropout | 0.2 |
| target_modules | `q_proj`, `k_proj`, `v_proj` |
| bias | none |
| init_lora_weights | true |
| task_type | CAUSAL_LM |

### 訓練結果（log 尾端，實測值）

| 指標 | 值 |
|---|---|
| 最終 train_loss | 1.759 |
| 最終 eval_loss（epoch 10） | 1.651 |
| train_runtime | 2.078e4 秒（約 5.77 小時） |
| train_samples_per_second | 126.2 |

## Crack Rate

| @K | Cracked | Rate |
|---|---|---|
| @1 | 159 / 5,000 | 3.18% |
| @10 | 348 / 5,000 | 6.96% |
| @100 | 576 / 5,000 | 11.52% |
| @1000 | 835 / 5,000 | 16.70% |

> 數據來源：`param_compare.md` §1.1（run_10 vs run_13 對照）。

## 與 run_10（id=5）比較

固定 LoRA/資料集/其餘超參數，唯一差異為 prompt template（id=5 有 JSON 包裝＋詳細指示；id=6 精簡純文字）。

| 指標 | run_10（id=5） | run_13（id=6） |
|---|---|---|
| 最終 train_loss | 1.545 | 1.759 |
| 最終 eval_loss | 1.649 | 1.651 |
| @1 | 3.10% | 3.18% |
| @10 | 7.20% | 6.96% |
| @100 | 11.56% | 11.52% |
| @1000 | 17.02% | 16.70% |

> loss 曲線幾乎完全重疊，crack rate 差距在四個 K 值方向不一致且皆 <3.3%，屬隨機波動範圍，
> 詳見 [param_compare.md](param_compare.md) §1.1 與對應圖表。
