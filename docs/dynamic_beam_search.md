# Dynamic Beam Search — 演算法文件

## 概覽

`dynamic_beam_search` 與 `dynamic_beam_search_Constrained_Decoding` 是本專案的純機率 beam search 實作，無對比懲罰。前者為通用版本，後者在前者基礎上加入字元類別與長度的 hard constraint。

兩者均位於 [util/search.py](../util/search.py)。

---

## 共用基礎設施

### KV Cache 管理（[util/search.py:23](../util/search.py#L23)）

```
info_cache  — prompt 的 KV cache（1 份，所有 beam 共用）
pw_cache    — 密碼部分的 KV cache（beam_width 份，每個 beam 獨立）
```

每次 forward pass 前：

```python
cache = _cache_concat(
    _expand_cache(beam.info_cache, batch),  # zero-copy broadcast（非複製）
    _reorder_cache(beam.pw_cache, parent_indices)
)
```

`_expand_cache` 用 `expand`（view，無實體複製）廣播 prompt KV cache；`_reorder_cache` 按父 beam 索引重排密碼 KV cache。forward 結束後，只截取密碼部分存入 `pw_cache`：

```python
pw_cache = _cache_slice(outputs.past_key_values, pw_slice_index[:l+1])
```

### `remap_logits`（[util/search.py:69](../util/search.py#L69)）

```python
filtered_logits = logits[:, :, vocab]  # 只保留自定義詞彙的 logits
```

將模型的 `vocab_size` 維 logits 壓縮為自定義詞彙維度（95 printable ASCII chars + EOS = 96），排除所有非法 token。

### `DBS_Beam`（[util/search.py:100](../util/search.py#L100)）

管理 beam search 狀態的資料類別：

| 屬性 | 形狀 | 說明 |
|---|---|---|
| `pw_idx` | `[search_width, l]` | 各 beam 目前已生成的 token ID 序列 |
| `beam_prob` | `[beam_width, 1]` | top beam_width 的累積 log-prob |
| `search_prob` | `[search_width, 1]` | top search_width 的累積 log-prob |
| `last_beam_index` | `[search_width]` | 各 search beam 對應的父 beam 索引 |
| `info_cache` | `DynamicCache` | prompt KV cache（1 份） |
| `pw_cache` | `DynamicCache` | 密碼 KV cache（beam_width 份） |
| `vocab_tensor` | `[vocab_size]` | 當前 step 的詞彙 tensor |

`update_by_prob(beam_width, search_width, probs, pw_cache)` 的核心邏輯：

```python
tot_probs = (beam_prob.reshape(-1, 1) + probs).reshape(-1)
# 形狀：[beam_width × vocab_size]（排除 EOS 欄）

search_prob, search_idx = topk(tot_probs, search_width)  # for EOS scan
beam_prob,   beam_idx   = topk(tot_probs, beam_width)    # for next step

# 解碼 beam 索引（哪個父 beam + 哪個字元）
parent = search_idx // (vocab_size - 1)
token  = search_idx %  (vocab_size - 1)
```

---

## `dynamic_beam_search`（[util/search.py:133](../util/search.py#L133)）

### 演算法流程

```
[Prompt forward pass]
  input_ids → model → logits → remap → log_softmax → word_probs[1, vocab-1]

[Loop l = 0 → max_length-1]
  beam.update_by_prob(beam_width[l], reserve_width, word_probs, pw_cache)
    → beam.pw_idx: [reserve_width, l+1]  (已生成序列)
    → beam.search_prob: [reserve_width, 1] (累積 log-prob)
  
  For each batch i (stride = batch_size):
    start, end = 計算當前 batch 的 beam 範圍
    cache = _cache_concat(_expand_cache(info), _reorder_cache(pw, parent_idx))
    outputs = model.forward(pw_idx[start:end, -1:], past_key_values=cache)

    if EOS log-prob >= eos_threshold AND l >= min_len - 1:
        eos_list.append((seq, beam_prob + eos_log_prob))

    if i < beam_forward_num:
        word_probs[start:end] = log_softmax(remap(vocab, logits))[:, :-1]
        pw_cache[start:end]   = _cache_slice(outputs.past_key_values)
```

### Beam / Search Width 上界調整

```python
beam_width_list[0] = min(beam_width_list[0], vocab_size - 1)
beam_width_list[l] = min(beam_width_list[l], beam_width_list[l-1] * (vocab_size - 1))
```

防止 beam 數超過實際可展開的候選數。

### EOS 收集策略

基於 `eos_threshold`（log 機率閾值）：任何 step 都可以發 EOS，只要其 log-prob 超過閾值。允許不同長度的密碼進入 `eos_list`。

### 參數說明

| 參數 | 型別 | 說明 |
|---|---|---|
| `beam_width_list` | `list[int]` | 每 step 的 beam 寬度（如 `[95, 1000×15]`） |
| `search_width_list` | `list[int]` | search beam 寬度；預設與 `beam_width_list` 同 |
| `vocab` | `list[int]` | 允許的 tokenizer token ID 列表（含 EOS） |
| `eos_threshold` | `float` | EOS 收集的最低機率（如 `0.001`） |
| `batch_size` | `int` | 每次 forward pass 的 beam 數 |
| `min_len` | `int` | 最短密碼長度（EOS 在 `l < min_len-1` 時被壓制） |
| `seg_separator_id` | `int` | id=4 template 的換行分隔符，輸出前去除 |

### 配置範例（`config/search.yaml`）

```yaml
search_type: dynamic_beam_search

dynamic_beam_search:
  beam_width: [ 95, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500 ]
  batch_size: 100
  prompt_template_id: 3
  vocab_limit: true
  precistion: half
  eos_threshold: 0.001
  max_guess_number: 1000
  min_len: 7
```

---

## `dynamic_beam_search_Constrained_Decoding`（[util/search.py:672](../util/search.py#L672)）

在 `dynamic_beam_search` 基礎上加入三個 hard constraint：

### 1. Per-Step Vocab Restriction

根據 `build_step_constraints(tags_str, vocab_dict, eos_id)` 將 Tags 展開為 per-step 字元集：

```
"char5|number3|special1"
→ step 0-4: alpha_ids   (52 chars)
→ step 5-7: digit_ids   (10 chars)
→ step 8:   special_ids (33 chars)
```

每個 step 的 `beam.vocab_tensor` 替換為當前字元集 + EOS：

```python
step_vocab_tensors[l] = torch.tensor(step_char_ids[l] + [eos_id])
beam.vocab_tensor = step_vocab_tensors[l]
```

`update_by_prob` 內的解碼（`vocab_tensor.shape[0] - 1`）因此自動對應當前字元集大小。

### 2. 跨 Step 的 Word Probs 銜接

Step `l` 的 forward pass 產生的 `word_probs` 供 step `l+1` 使用，因此 remap 必須用 **next step 的 vocab**：

```python
# step l 的 forward 內（非最後 step）
logits = remap_logits(next_vtensor, outputs.logits)[:, -1, :]
# next_vtensor = step_vocab_tensors[l+1]
```

### 3. EOS Hard Enforcement

| Step | EOS 行為 |
|---|---|
| 非最後 step | 完全不收集 EOS（beam 不允許提前結束） |
| 最後 step | 強制所有存活 beam 發 EOS；EOS log-prob 用 **full-vocab** `log_softmax` 計算（保證機率比較一致性） |

```python
if is_last_step:
    eos_log_probs = log_softmax(outputs.logits[:, -1, :], dim=-1)[:, eos_id]
    # 不用 restricted vocab，直接從 full logits 取 EOS 的機率
```

### Per-Step Beam Width 上界

```python
step_bws[0] = min(beam_width, len(step_char_ids[0]))
step_bws[l] = min(beam_width, step_bws[l-1] * len(step_char_ids[l]))
```

例：`number6`（digit-only）：step_bws 上界為 10 → 100 → 1000 → 1000…

### 限制

只支援 backoff structural tags：

| Tag | 支援 | 原因 |
|---|---|---|
| `numberN`, `charN`, `specialN`, `mixedN` | ✅ | 長度與字元集均在 tag 中編碼 |
| `nn`, `vv0`, `fname`… | ❌ | Tag 不編碼長度，無法展開 per-step 約束 |

含任何 pos/semantic tag 時，`build_step_constraints` 回傳 `(None, None)`，呼叫端應 fallback 到 `dynamic_beam_search`。

### 參數說明

| 參數 | 型別 | 說明 |
|---|---|---|
| `tags_str` | `str` | 來自 JSONL 的 Tags 欄位，如 `"char5\|number3\|special1"` |
| `vocab_dict` | `dict[str, int]` | `get_alpa(tokenizer)` 的回傳值（char → token ID） |
| `eos_id` | `int` | `tokenizer.eos_token_id` |
| `beam_width` | `int` | 目標 beam 寬度（各 step 依字元集自動限制上界） |
| `search_width` | `int` | search beam 寬度，預設與 `beam_width` 同 |
| `batch_size` | `int` | 每次 forward pass 的 beam 數 |

### 配置範例（`config/search.yaml`）

```yaml
search_type: constrained_beam_search

constrained_beam_search:
  beam_width: 1000          # 單一 int（非 list）
  search_width: 1000
  batch_size: 100
  prompt_template_id: 3
  precistion: half
  max_guess_number: 1000
  fallback_to_dynamic: true
  output_path: gen
  output_file_name: constrained_beam_search_results.jsonl
```

---

## 兩者比較

| | `dynamic_beam_search` | `dynamic_beam_search_Constrained_Decoding` |
|---|---|---|
| 字元類別合規 | ❌ 可能生成錯誤字元 | ✅ hard enforce |
| 長度合規 | ❌ 可能過短/過長 | ✅ 完全精確（backoff） |
| EOS 策略 | threshold-based（任何 step） | 最後 step 強制（其餘禁止） |
| 適用 tag 類型 | 全部 | 僅 backoff |
| `beam_width` 參數型別 | `list[int]`（per-step） | `int`（全域上界） |
| Vocab 參數 | `list[int]`（flat list） | `dict[str, int]`（char → id） |
| 計算效率 | 每 step 95 chars 全探索 | 每 step 只探索當前字元集 |

---

## 效能注意事項

- `_expand_cache`（zero-copy view）：避免每次 forward 實體複製 prompt KV cache `batch_size` 份。`_cache_concat` 之後的 `torch.cat` 會創造一個新的連續 tensor，但中間不再有多餘的 `index_select` 複製。
- `batch_size` 建議：`dynamic_beam_search` 的合理值為 100；更大的 batch_size 雖然減少 forward 次數，但增加 KV cache 組合的記憶體壓力。
- `search_width_list > beam_width_list`：search extension beams 只用於 EOS 偵測，不產生 `word_probs`，overhead 相對低；但同樣需要 forward pass，建議保守設定。
