# PassLLM Bug Fixes

## 背景

PassLLM 是獨立執行的密碼猜測框架（`models/passllm/`），資料來源與本專案共用。在評估其訓練/評估流程時發現以下 bug，記錄修正過程。

---

## 問題評估

### 訓練

| # | 嚴重度 | 問題 | 是否修正 |
|---|--------|------|---------|
| 1 | Bug（潛伏） | `process_val_targeted` 雙重參數名稱錯誤 | ✅ |
| 2 | Bug | `Dataset.from_pandas` 的 `split` 型態錯誤 | ✅ |
| 3 | Missing | 訓練資料不在 repo | 待補 |

### 評估

| # | 嚴重度 | 問題 | 是否修正 |
|---|--------|------|---------|
| 4 | Critical | `predict_next` 回傳 3 值但 callers 解包 2 → wsgen/dsgen crash | ✅ |
| 5 | Silent | eval config `prompmt_template_id` typo，fallback 到 0（剛好正確） | ✅ |

---

## 修正紀錄

### Fix 1 — `process_val_targeted` 參數名稱錯誤

**檔案**：`src/utils/tokenize.py`

**問題**：三方參數名稱不一致：
- `train.py` 呼叫 `process_val_targeted` 時傳入 `vocab=self.vocab`
- `process_val_targeted` 定義的參數名為 `limit_vocab`（接收失敗）
- `process_val_targeted` 內部轉傳給 `process_train_targeted` 時用 `limit_vocab=limit_vocab`，但後者期望 `vocab=`

雖然目前兩個 training config 的 `validation_data` 都為空（走 `train_test_split` 分支），`process_val_targeted` 不會被呼叫，但只要 `validation_path` 一設值就會立即 crash。

**修正**：將 `process_val_targeted` 的參數名與內部轉傳統一改為 `vocab`。

```python
# Before
def process_val_targeted(example, tokenizer, limit_vocab, prompt_id, ...):
    return process_train_targeted(..., limit_vocab=limit_vocab, ...)

# After
def process_val_targeted(example, tokenizer, vocab, prompt_id, ...):
    return process_train_targeted(..., vocab=vocab, ...)
```

---

### Fix 2 — `Dataset.from_pandas` 的 `split` 型態錯誤

**檔案**：`src/model/train.py`

**問題**：`datasets 3.5.0` 的 `Dataset.from_pandas` 期望 `split` 為字串（`str` 或 `NamedSplit`），傳入 list `["train"]` 會導致型態錯誤，使 trawling 模式訓練無法啟動。

**修正**：

```python
# Before
self.train_ds = Dataset.from_pandas(data, split=["train"])

# After
self.train_ds = Dataset.from_pandas(data, split="train")
```

---

---

### Fix 3 — `predict_next` 多回傳 `hidden_states` 導致解包 crash

**檔案**：`src/search/search.py`

**問題**：`predict_next` 在加入 contrastive 功能時被改為回傳 3 個值（`word_prob, past_key_values, hidden_states`），但所有呼叫它的地方（`_width_search`、`get_prefix`）都只解包 2 個，導致 `ValueError: too many values to unpack`。

`contrastive_search` 和 `dynamic_beam_search` 本身直接呼叫 `model.forward()`，不使用 `predict_next`，故 targeted eval 不受影響。

**修正**：移除 `output_hidden_states=True` 與多餘的第三個回傳值。

```python
# Before
outputs = model.forward(..., output_hidden_states=True, ...)
return word_prob, outputs.past_key_values, outputs.hidden_states

# After
outputs = model.forward(..., output_hidden_states=False, ...)
return word_prob, outputs.past_key_values
```

---

### Fix 4 — eval config `prompmt_template_id` typo

**檔案**：`config/evaluation_126_csdn_config.ini`、`config/evaluation_126_csdn_contrastive_config.ini`

**問題**：兩個 eval config 的 key 都拼成 `prompmt_template_id`（多一個 `m`），但 `main.py` 讀 `prompt_template_id`，導致設定值被靜默忽略、永遠 fallback 到 `0`。目前剛好兩者都打算用 template 0，所以行為正確但設定無效。

**修正**：將兩個 ini 中的 key 改為 `prompt_template_id`。

---

---

### Fix 5 — 評估結束無最終彙整輸出

**檔案**：`src/utils/utils.py`、`src/model/eval.py`

**問題**：
1. `pm_guesser._save()` 每 `log_interval` 筆才寫一次，若最後一批不足整數倍則不寫入（資料遺漏）
2. 評估結束後沒有任何最終 crack rate 彙整，只能從 `log.txt` 最後一行手動讀取

**修正**：

在 `pm_guesser` 加入 `finalize()` 方法：
- 沖出剩餘未存的 entries
- 印出最終彙整到 console 與 `log.txt`

```
====================================================
 Evaluation Complete  |  Total: 500
====================================================
  Crack @1     :     12 / 500  (2.40%)
  Crack @10    :     48 / 500  (9.60%)
  Crack @100   :    110 / 500  (22.00%)
  Crack @1000  :    185 / 500  (37.00%)
====================================================
```

在 `GuessLLM_Evaluator.eval()` 結尾加 `self.guesser.finalize()` 呼叫。

---

## 待處理

- [ ] **資料準備**：補充 `data/rockyou/rockyou_train_100W_filter.txt`、`data/126_csdn/126_csdn_train.json`
