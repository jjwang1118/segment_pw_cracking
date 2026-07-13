# Eval Report: Mistral-7B-v0.1 · Template id=5 · constrained_beam_search（COMB dataset）

## 實驗設定

| 項目 | 值 |
|---|---|
| 模型 | Mistral-7B-v0.1 |
| LoRA | `checkpoints/Mistral-7B-v0.1/run_10/lora_final` |
| LoRA rank / alpha / target_modules | r=16, alpha=32, [q_proj, k_proj, v_proj]（`train_config.yaml` 預設值） |
| 訓練 Template ID | 5 |
| 推論 Template ID | 5 |
| 評估筆數 | 5,000 |
| Max guess | 1,000 |
| 搜尋法（primary） | `constrained_beam_search` |
| 搜尋法（fallback） | `dynamic_beam_search`（當 tags 含 pos/pos_semantic 時） |
| 測試集 | `datasets/processed/semanticPCFG/COMB/backoff/split/test_data.jsonl`（訓練資料同為 COMB，非 000webhost） |
| 來源 log | `results/eval/eval-258985.out` |

## Crack Rate

| @K | Cracked | Rate |
|---|---|---|
| @1 | 155 / 5,000 | 3.10% |
| @10 | 360 / 5,000 | 7.20% |
| @100 | 578 / 5,000 | 11.56% |
| @1000 | 851 / 5,000 | 17.02% |

## 結果圖表

![Crack Rate & Tag Distribution](../../gen/results/id5_run10_Mistral-7B_id5_COMB_constrained_beam_search_result.png)

## 破解密碼的 Tag 類型分佈

（分母為 COMB 測試集：純 backoff 1,773 筆 / 含 pos-pos_semantic 3,227 筆，與 000webhost 測試集比例不同）

| Tag 類型 | 筆數 | 比例 |
|---|---|---|
| 純 backoff tag | 44 | 5.2% |
| 含 pos / pos_semantic tag | 807 | 94.8% |

> **觀察：** COMB 資料集（訓練+測試皆為 COMB）的 @1000 破解率（17.02%）高於同 template（id=5）在 000webhost 上的 run_6/run_7（15.04% / 14.76%），推測與 COMB 資料量更大、密碼組成更多樣有關；破解密碼中含 pos/pos_semantic tag 的比例（94.8%）也高於 000webhost 上的結果（約 90%），需交叉比對訓練/測試資料集是否一致才能公平比較不同 run 之間的破解率。
