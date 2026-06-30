# Contrastive Search — 演算法文件

## 概覽

`contrastive_search` 與 `contrastive_search_Constrained_Decoding` 是本專案的多樣性導向 beam search 實作。在純機率 beam search 的基礎上，對 hidden state 軌跡「重複」的 beam 施加懲罰，使候選密碼集在結構上更多樣。後者額外加入字元類別與長度的 hard constraint。

兩者均位於 [util/search.py](../util/search.py)。

---

## 核心概念：對比懲罰（Contrastive Penalty）

### 問題

純 beam search 傾向選擇高機率路徑，導致 top-K 候選集中在少數幾個接近的字串（例如 `alice99!` / `alice98!` / `alice97!`），未能充分探索解空間。

### 解法

對每個 beam，記錄其過去所有位置的 hidden state（`acc_hidden_state`）。在當前位置生成新 token 前，計算當前 hidden state 與歷史的最大餘弦相似度，作為懲罰：

```
score(beam, token) = (1 - α) × logP(token | context) − α × max_cos_sim(h_current, H_history)
```

- `α`（`contrastive_alpha`）：懲罰強度，預設 0.6
- `max_cos_sim`：當前 hidden state 與該 beam 歷史中所有 hidden states 的最大餘弦相似度
- 分數越高 → 越符合「高機率 + 低重複性」

### 懲罰的作用層次

懲罰是 **per-beam** 的，而非 per-token：同一個 beam 的所有候選 token 被施加相同大小的懲罰。因此：

- **beam 內部**：token 相對機率排序不變
- **跨 beam**：hidden state 軌跡越「重複」的 beam，其整體分數被壓低，讓其他 beam 有更多機會進入 top-K

效果是在 beam set 層次促進多樣性，而非對個別 token 做細粒度篩選。

---

## `DBS_beam_contrastive_search`（[util/search.py:264](../util/search.py#L264)）

繼承 `DBS_Beam` 的 beam 狀態管理，額外維護 hidden state 歷史。

### 新增屬性

| 屬性 | 形狀 | 說明 |
|---|---|---|
| `acc_hidden_state` | `[beam_width, history_len, hidden_dim]` | 每個 beam 的 hidden state 歷史（沿 seq 維度累積） |

初始化時以 prompt 的最後一個 token 的 hidden state 為起點：

```python
self.acc_hidden_state = initial_hidden.unsqueeze(1)  # [1, 1, hidden_dim]
```

### `accumulate_hidden(hidden_states)`

```python
# hidden_states: [beam_width, hidden_dim]
new_hidden = hidden_states.unsqueeze(1)              # [beam_width, 1, hidden_dim]
self.acc_hidden_state = cat([self.acc_hidden_state, new_hidden], dim=1)
# → [beam_width, history_len+1, hidden_dim]
```

### `compute_contrastive_penalty(current_hidden, beam_indices, alpha)`

```python
# current_hidden: [batch, hidden_dim]  — 當前位置的 hidden state
# beam_indices:   [batch]              — 索引到 acc_hidden_state

beam_histories = acc_hidden_state[beam_indices]      # [batch, history, hidden_dim]

current_norm = normalize(current_hidden, p=2, dim=-1)
history_norm = normalize(beam_histories,  p=2, dim=-1)

# 計算餘弦相似度矩陣 [batch, history]
similarity = bmm(
    current_norm.unsqueeze(1),       # [batch, 1, hidden_dim]
    history_norm.transpose(1, 2)     # [batch, hidden_dim, history]
).squeeze(1)

max_similarity = similarity.max(dim=-1)[0]   # [batch]
penalty = alpha * max_similarity             # [batch]
```

### `update_by_prob` 中的 Hidden State 管理

```python
if hidden_states is not None:
    # 按父 beam 索引重排歷史，再追加當前 hidden state
    self.acc_hidden_state = self.acc_hidden_state[self.beam_parent_index]
    selected_hidden = hidden_states[self.beam_parent_index]
    self.accumulate_hidden(selected_hidden)
else:
    # 無 hidden states 時（初始 step），expand 歷史以匹配 beam_width
    self.acc_hidden_state = self.acc_hidden_state.expand(beam_width, -1, -1).clone()
```

---

## `contrastive_search`（[util/search.py:391](../util/search.py#L391)）

### 演算法流程

```
[Prompt forward pass]
  output_hidden_states=True
  initial_hidden = hidden_states[-1][:, -1, :]   # [1, hidden_dim]
  word_probs = log_softmax(remap(vocab, logits))[:, :-1]

[初始 beam 展開（l=0 前）]
  beam.update_by_prob(bw[0], sw[0], word_probs, None)
  # acc_hidden_state expand 為 [bw[0], 1, hidden_dim]

[Loop l = 0 → max_length-1]
  For each batch i:
    need_hidden = use_contrastive AND i < beam_forward_num
    outputs = model.forward(..., output_hidden_states=need_hidden)

    if need_hidden:
      current_hidden = outputs.hidden_states[-1][:, -1, :]
      penalty = beam.compute_contrastive_penalty(current_hidden, beam_indices, α)
      hidden_states_batch.append(current_hidden)
    else:
      penalty = zeros(batch)

    batch_word_probs[:, :-1] = (1-α) × batch_word_probs[:, :-1] − penalty
    # 懲罰套用在 word_probs（下一 step 的候選機率）

    if l >= min_len - 1 AND eos_log_prob >= eos_threshold:
      eos_list.append(...)

  [End of step l]
  beam.update_by_prob(bw[l+1], sw[l+1], word_probs, pw_cache, all_hidden)
  # all_hidden = cat(hidden_states_batch)，更新 acc_hidden_state
```

### `output_hidden_states` 策略

| Batch 類型 | `output_hidden_states` | 原因 |
|---|---|---|
| Beam batches（`i < beam_forward_num`） | `True`（僅當 `use_contrastive=True`） | 需要 hidden state 計算 penalty |
| Search-extension batches（`i >= beam_forward_num`） | `False` | 僅用於 EOS 偵測，不需 penalty |

這避免對 Qwen3-4B 36 層的全部 hidden states 做不必要的 materialize 與傳輸。

### EOS 收集策略

與 `dynamic_beam_search` 相同：threshold-based，任何 step 都可發 EOS（`l >= min_len - 1` 且 log-prob >= threshold）。

### 參數說明

| 參數 | 型別 | 說明 |
|---|---|---|
| `beam_width_list` | `list[int]` | 每 step 的 beam 寬度 |
| `search_width_list` | `list[int]` | search beam 寬度 |
| `vocab` | `list[int]` | 允許的 token ID 列表 |
| `eos_threshold` | `float` | EOS 收集閾值 |
| `use_contrastive` | `bool` | 是否啟用 hidden state 懲罰 |
| `contrastive_alpha` | `float` | 懲罰強度 α（0=純機率，1=純多樣性） |
| `batch_size` | `int` | 每次 forward pass 的 beam 數 |
| `min_len` | `int` | 最短密碼長度 |

### 配置範例（`config/search.yaml`）

```yaml
search_type: contrastive_search

contrastive_search:
  beam_width: [ 95, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500 ]
  batch_size: 500
  prompt_template_id: 3
  vocab_limit: true
  precistion: half
  eos_threshold: 0.0001
  max_guess_number: 50
  min_len: 8
  use_contrastive: true
  contrastive_alpha: 0.6
```

---

## `contrastive_search_Constrained_Decoding`（[util/search.py:855](../util/search.py#L855)）

將 `contrastive_search` 的多樣性懲罰與 `dynamic_beam_search_Constrained_Decoding` 的 hard constraint 結合。

### 設計原則

1. **字元類別與長度 hard enforce**：與 `dynamic_beam_search_Constrained_Decoding` 完全相同（per-step vocab tensor + 最後 step 強制 EOS）
2. **對比懲罰**：與 `contrastive_search` 相同（`acc_hidden_state` + `compute_contrastive_penalty`）
3. **`use_contrastive=False` 時直接 delegate**：避免重複邏輯
4. **`output_hidden_states` 最小化**：只在需要的 batch 與 step 開啟

### 演算法流程

```
[Prompt forward pass]
  output_hidden_states=True
  initial_hidden = hidden_states[-1][:, -1, :]

[初始 beam 展開（l=0 前）]
  beam.vocab_tensor = step_vocab_tensors[0]
  beam.update_by_prob(bw0, sw0, word_probs, None)
  # acc_hidden_state: [bw0, 1, hidden_dim]

[Loop l = 0 → total_length-1]
  # 字元集約束
  cur_vtensor = step_vocab_tensors[l]
  is_last_step = (l == total_length - 1)

  For each batch i:
    need_hidden = (i < beam_forward_num) AND (NOT is_last_step)
    outputs = model.forward(..., output_hidden_states=need_hidden)

    if is_last_step:
      # 強制 EOS：用 full-vocab log_softmax 取 P(EOS)
      eos_log_probs = log_softmax(outputs.logits[:, -1, :])[:, eos_id]
      eos_list.append(...)  # 所有存活 beam 全部收集
    else:
      if need_hidden:
        penalty = compute_contrastive_penalty(current_hidden, beam_indices, α)
        hidden_states_batch.append(current_hidden)
      else:
        penalty = zeros(batch)

      # 用 NEXT step 的 vocab remap（hard constraint 關鍵）
      logits = remap_logits(next_vtensor, outputs.logits)[:, -1, :]
      batch_word_probs = log_softmax(logits)
      batch_word_probs[:, :-1] = (1-α) × batch_word_probs[:, :-1] − penalty

  [End of step l，若非最後 step]
  beam.vocab_tensor = step_vocab_tensors[l+1]
  beam.update_by_prob(next_bw, next_reserve, word_probs, pw_cache, all_hidden)
```

### `need_hidden` 最佳化

```python
need_hidden = (i < beam_forward_num) and (not is_last_step)
```

最後 step 完全不需要 hidden states（只收集 EOS），全部 forward 都省去 hidden state 傳輸。

### `use_contrastive=False` 的處理

```python
if not use_contrastive:
    return dynamic_beam_search_Constrained_Decoding(
        model=model, input_ids=input_ids, tags_str=tags_str, ...
    )
```

不重複實作，直接轉交給純 beam 版本。

### 限制

與 `dynamic_beam_search_Constrained_Decoding` 相同：只支援 backoff structural tags（`numberN` / `charN` / `specialN` / `mixedN`）。含 pos/semantic tag 時，呼叫端應 fallback 到 `contrastive_search`。

### 參數說明

| 參數 | 型別 | 說明 |
|---|---|---|
| `tags_str` | `str` | pipe-separated Tags，如 `"char5\|number3\|special1"` |
| `vocab_dict` | `dict[str, int]` | char → token ID 對應 |
| `eos_id` | `int` | `tokenizer.eos_token_id` |
| `beam_width` | `int` | 目標 beam 寬度（各 step 依字元集自動限制） |
| `search_width` | `int` | search beam 寬度，預設與 `beam_width` 同 |
| `batch_size` | `int` | 每次 forward pass 的 beam 數 |
| `use_contrastive` | `bool` | 啟用對比懲罰（`False` 時 delegate 到 DBS） |
| `contrastive_alpha` | `float` | 懲罰強度 α |

### 配置範例（`config/search.yaml`）

```yaml
search_type: constrained_contrastive_search

constrained_contrastive_search:
  beam_width: 1000
  search_width: 1000
  batch_size: 100
  prompt_template_id: 3
  precistion: half
  max_guess_number: 1000
  use_contrastive: true
  contrastive_alpha: 0.6
  fallback_to_dynamic: true
  output_path: gen
  output_file_name: constrained_contrastive_search_results.jsonl
```

---

## 四個函式總覽

| | `dynamic_beam_search` | `dynamic_beam_search`<br>`_Constrained_Decoding` | `contrastive_search` | `contrastive_search`<br>`_Constrained_Decoding` |
|---|:---:|:---:|:---:|:---:|
| 字元類別 hard enforce | ❌ | ✅ | ❌ | ✅ |
| 長度 hard enforce | ❌ | ✅ | ❌ | ✅ |
| Hidden state 多樣性懲罰 | ❌ | ❌ | ✅ | ✅ |
| EOS 策略 | threshold | 最後 step 強制 | threshold | 最後 step 強制 |
| 適用 tag | 全部 | backoff only | 全部 | backoff only |
| `beam_width` 型別 | `list[int]` | `int` | `list[int]` | `int` |
| Vocab 參數 | `list[int]` | `dict[str, int]` | `list[int]` | `dict[str, int]` |
| `output_hidden_states` | ❌ | ❌ | beam batches only | beam batches only（非最後 step） |

---

## 效能考量

### `output_hidden_states` 開銷

Qwen3-4B 有 36 層。`output_hidden_states=True` 迫使模型保留並回傳全部 36 層的 activations。對 `batch_size=500` 的 forward pass：

```
500 beams × 36 layers × hidden_dim × dtype_size ≈ 數十 MB / forward pass
```

透過 `need_hidden` flag，只有真正需要計算 penalty 的 batch 才開啟此選項，省去 search-extension beams 與最後 step 的 hidden state overhead。

### Prompt KV Cache 廣播

`_expand_cache` 用 `expand`（zero-copy view）廣播 prompt KV cache，取代舊版 `_reorder_cache(info_cache, zeros_tensor)` 的 `index_select`（實體複製）。`_cache_concat` 的 `torch.cat` 會創造最終連續 tensor，但減少了一次 `batch_size` 倍的中間記憶體分配。

### `acc_hidden_state` 記憶體增長

隨生成長度線性增長：`[beam_width, length, hidden_dim]`。以 `beam_width=1000`、`length=16`、`hidden_dim=2048`（float16）估算：

```
1000 × 16 × 2048 × 2 bytes ≈ 65 MB
```

在 12GB 顯卡上可接受，但需留意長密碼（`length > 20`）或超大 beam_width 的情境。
