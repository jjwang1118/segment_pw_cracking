# Cross-site 實驗



## Reused

### COMB_MIX → Collection1

訓練站 COMB_MIX，跨站測試 Collection1（sibling + account 線索）；5,000 筆、Mistral-7B-v0.1 + LoRA、max_guess=1,000。

| K | StructLLM（run_25, COMB_MIX→Collection1） | Passllm Reused ‡ | PassBERT |
|---:|---:|---:|---:|
| @1    | 21.56% (1,078) | 0.00% (0) | 2.20% (110) |
| @10   | 36.56% (1,828) | 9.56% (478) | 7.28% (364) |
| @100  | 45.86% (2,293) | 23.80% (1,190) | 13.44% (672) |
| @1000 | 52.14% (2,607) | 31.90% (1,595) | 18.40% (920) |

> ‡ Passllm Reused 來源：`results/passllm/cross-site/COMBMIX_Collection1/eval-387031_pii_sibling.out`（分母 5,000；另有 @50 19.72% (986)、@500 29.96% (1,498)）。

![Cross-site Reused COMB_MIX→Collection1](../../gen/results/id9_run25_Mist7B_COMBMIX_to_Collection1_crosssite_reused_result.png)

---

## PII + Sibling



