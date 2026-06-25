# Constrained Decoding — 字元類別與長度硬性約束

## 問題背景

Prompt id=3 透過自然語言描述告知模型每個 segment 的字元類別與長度，例如：

```
"<SEG2>": "A sequence of exactly 6 digit characters (0-9)."
```

但 LLM 是機率型生成模型，文字描述只是 soft guidance。實際推理時模型可能提早發出 EOS，導致 `number6` 只生成 1 個數字。Constrained Decoding 透過在 beam search 每個 step 動態限制可選 token，將 soft guidance 升級為 hard enforcement。

---

## 核心概念

### 問題分解

Tags 字串（如 `"char5|number3|special1"`）已經完整編碼了每個 segment 的資訊：

| Tag 類別 | 字元集 | 長度 |
|---|---|---|
| `backoff` (`numberN`, `charN`, `specialN`, `mixedN`) | ✅ 確定 | ✅ 確定（N 直接在 tag 內） |
| `pos` (`nn`, `vv0`, `fname`…) | ✅ 只知是 alpha | ❌ 未知 |

對 **backoff** tags，可以將 Tags 展開成逐步的字元集約束：

```
"char5|number3|special1"
↓
step 0 → alpha only
step 1 → alpha only
step 2 → alpha only
step 3 → alpha only
step 4 → alpha only
step 5 → digit only
step 6 → digit only
step 7 → digit only
step 8 → special only
```

### Vocab 替換

現有 beam search 在每個 step 使用同一個 `vocab_list`（95 chars + EOS）。Constrained Decoding 在 step `l` 改用 `step_vocab_tensors[l]`：

```
非 digit 位置：step_vocab_tensor = [digit_0, digit_1, ..., digit_9, EOS]
alpha 位置：   step_vocab_tensor = [a, b, ..., z, A, B, ..., Z, EOS]
special 位置：  step_vocab_tensor = [!, @, #, ..., EOS]
```

`remap_logits` 每次只從模型輸出中提取當前允許字元的 logits，其餘字元的機率被完全排除在 softmax 之外。

### EOS 處理

- **非最後 step**：完全不收集 EOS，beam 不允許提前結束
- **最後一個 step**：強制對所有存活 beam 收集 EOS，以 full-vocab log_softmax 計算 P(EOS) 用於排序

這保證每個候選密碼的長度恰好等於 tags 指定的總長度。

---

## 實作細節

### `build_step_constraints` ([util/search.py:629](../util/search.py#L629))

將 Tags 字串解析為 per-step 的 token ID 列表：

```python
step_char_ids, total_length = build_step_constraints(tags_str, vocab_dict, eos_id)
# step_char_ids: List[List[int]]  — 每個 step 允許的 tokenizer token IDs
# total_length:  int              — 密碼的確切字元數
# 若含 pos/semantic tag → 回傳 (None, None)
```

字元集分類方式（基於 Python 內建判斷）：

```python
digit_ids   = [tid for c, tid in vocab_dict.items() if c.isdigit()]   # 10 chars
alpha_ids   = [tid for c, tid in vocab_dict.items() if c.isalpha()]   # 52 chars
special_ids = [tid for c, tid in vocab_dict.items() if not c.isalnum()] # 33 chars
any_ids     = list(vocab_dict.values())                                # 95 chars
```

### `dynamic_beam_search_Constrained_Decoding` ([util/search.py:672](../util/search.py#L672))

在 `dynamic_beam_search` 基礎上的三個核心修改：

#### 1. Per-step Beam Width 上界

因為每個 step 的 vocab 比 95 小，可展開的 beam 數受字元集大小限制：

```python
step_bws[0] = min(beam_width, len(step_char_ids[0]))
step_bws[l] = min(beam_width, step_bws[l-1] * len(step_char_ids[l]))
```

例如 `number6`（digit-only, 10 chars）：step_bws 上界為 10, 100, 1000, 1000…

#### 2. Vocab Tensor 逐 step 更換

`DBS_Beam.update_by_prob` 內部以 `self.vocab_tensor.shape[0] - 1` 做 beam 索引解碼。在每個 step 前更新：

```python
beam.vocab_tensor = step_vocab_tensors[l]
beam.update_by_prob(bw, reserve_width, word_probs, pw_past_key_values)
```

#### 3. Word Probs 跨 step 銜接

Forward pass 在 step `l` 產生的 `word_probs` 將用於 step `l+1`，因此必須用 **next step 的 vocab** 做 remap：

```python
# step l 的 forward pass 內
logits = remap_logits(next_vtensor, outputs.logits)[:, -1, :]   # next_vtensor = step_vocab_tensors[l+1]
word_probs = cat([word_probs, log_softmax(logits)[:, :-1]])      # 排除 EOS 欄
```

最後一個 step 不需要 `word_probs`，改為強制收集 EOS：

```python
if is_last_step:
    eos_log_probs = log_softmax(outputs.logits[:, -1, :], dim=-1)[:, eos_id]
    batch_eos_probs = beam.search_prob[start:end, 0] + eos_log_probs
    eos_list.extend(zip(eos_seqs, batch_eos_probs))
```

---

## 使用方式

### 在 `run_eval.py` 中呼叫

```python
from util.search import (
    dynamic_beam_search_Constrained_Decoding,
    build_step_constraints,
)

step_char_ids, total_len = build_step_constraints(
    entry["Tags"], vocab_dict, eos_id
)

if step_char_ids is not None:
    # 全 backoff → 使用 constrained decoding
    raw_results = dynamic_beam_search_Constrained_Decoding(
        model=model,
        input_ids=input_ids,
        tags_str=entry["Tags"],
        vocab_dict=vocab_dict,
        eos_id=eos_id,
        batch_size=batch_size,
        beam_width=beam_width,
    )
else:
    # 含 pos/semantic tag → fallback 到原版 beam search
    raw_results = dynamic_beam_search(...)
```

### 參數說明

| 參數 | 說明 | 預設 |
|---|---|---|
| `tags_str` | 來自 JSONL 的 `Tags` 欄位，如 `"char5\|number3\|special1"` | 必填 |
| `vocab_dict` | `get_alpa(tokenizer)` 的回傳值（char → token ID） | 必填 |
| `eos_id` | `tokenizer.eos_token_id` | 必填 |
| `beam_width` | 目標 beam 寬度（每 step 依字元集大小自動限制上界） | 1000 |
| `search_width` | search beam 寬度，預設與 `beam_width` 相同 | None |

---

## 適用範圍與限制

### 完全支援：backoff tags

| Tag | 字元集 | 長度 | Constrained |
|---|---|---|---|
| `numberN` | digit (0-9) | N | ✅ |
| `charN` | alpha (a-z A-Z) | N | ✅ |
| `specialN` | special (!@#…) | N | ✅ |
| `mixedN` | 全部 95 chars | N | ✅ (長度約束，無字元集約束) |

### 不支援：pos / semantic tags

| Tag | 字元集 | 長度 | 原因 |
|---|---|---|---|
| `nn`, `vv0`, `fname`… | alpha | ❌ 未知 | Tag 不編碼長度 |

含任何 pos/semantic tag 時，`build_step_constraints` 回傳 `(None, None)`，呼叫端應 fallback 到 `dynamic_beam_search`。

### 注意事項

- `mixed` tag 的字元集約束為「任意 95 chars」，等同無字元集限制，但長度仍被 hard enforce
- 不同於原版 `dynamic_beam_search` 的 `beam_width_list`（可逐 step 設定），此函式接受單一 `beam_width` 值，各 step 的上界由 tag 結構自動決定
- EOS log-prob 使用 full-vocab softmax 計算（非 restricted vocab），保證機率比較的一致性

---

## 效益分析

| | 原版 `dynamic_beam_search` | `dynamic_beam_search_Constrained_Decoding` |
|---|---|---|
| 字元類別合規 | ❌ 可能生成錯誤字元 | ✅ hard enforce |
| 長度合規 | ❌ 可能過短 / 過長 | ✅ 完全精確（backoff） |
| 有效候選比率 | 低（含大量結構不合規候選） | 100% 結構合規 |
| 計算效率 | 每 step 95 chars 全探索 | 每 step 只探索當前字元集（如 digit=10）|
| 適用 tag 類型 | 全部 | 僅 backoff |
