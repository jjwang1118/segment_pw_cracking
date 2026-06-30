# Qwen vs Mistral 處理方法

本專案目前同時在用兩個模型家族跑實驗：`Qwen3-4B`（原始預設模型，tiktoken tokenizer）與 `Mistral-7B-v0.1`（新增的對照實驗，SentencePiece tokenizer）。兩者共用同一套 pipeline（`run_train.py` / `run_eval.py` / `run_search.py`），但因 tokenizer 家族不同，部分底層程式碼需要做 model-aware 的分流處理。本文記錄這些差異點，供後續新增模型或除錯時參考。

---

## 1. Tokenizer 差異是唯一的核心分歧

| 項目 | Qwen3-4B | Mistral-7B-v0.1 |
|---|---|---|
| Tokenizer 家族 | tiktoken (BPE) | SentencePiece (SPM) |
| 單字元 token | 每個可印字元有專屬 token，直接 decode 乾淨 | 字元以 `▁X`（word-initial，含空格前綴）形式編碼 |
| 組合 decode 行為 | `decode([ID_d, ID_r])` → `"dr"`（無空格） | `decode([▁d, ▁r])` → `"d r"`（插入空格） |

模型載入、LoRA 套用、prompt template（`src/prompt_template.py`）都是 model-agnostic，純文字操作，不受 tokenizer 家族影響。**唯一**需要分流的是「逐字元密碼 ↔ token ID」的雙向映射，因為訓練與推論都要求把密碼拆成單一字元 token 序列。

---

## 2. `get_alpa()` — 95 字元詞表的雙策略偵測

檔案：[util/pw_tokenize.py](../util/pw_tokenize.py)

```python
_p1 = tokenizer("d", add_special_tokens=False)["input_ids"][-1]
_p2 = tokenizer("r", add_special_tokens=False)["input_ids"][-1]
_is_spm = tokenizer.decode([_p1, _p2]) != "dr"
```

用「兩字元組合 decode」探測 tokenizer 家族，而非單字元探測——因為 `decode([▁d])` 單獨 decode 也會回傳 `"d"`（無空格，SPM 在開頭不加前綴空格），只有組合 decode 才會暴露空格插入行為，是唯一可靠的判別方式（曾經因用單字元探測導致誤判，已於 `docs/logs/20260629_modify.md` 修正）。

判別結果目前兩個分支實作相同（直接查表 `tokenizer(w)["input_ids"][-1]`），差異只在於後續推論時是否需要去除空格（見下節）——保留分流是因為 SPM 分支的 `▁X` token ID 必須與 `encode_limit()` 訓練端用的映射完全一致，否則訓練目標與推論詞表會對不上。

---

## 3. 推論輸出去空格 — `run_eval.py` 的 `_needs_space_strip`

檔案：[run_eval.py:122-130](../run_eval.py)

```python
_pd, _pr = vocab_dict.get('d'), vocab_dict.get('r')
_needs_space_strip = bool(
    _pd is not None and _pr is not None
    and tokenizer.decode([_pd, _pr]) != "dr"
)
...
decoded = tokenizer.decode(seq.tolist(), skip_special_tokens=True)
if _needs_space_strip:
    decoded = decoded.replace(" ", "")
```

與 `get_alpa()` 用同一種兩字元組合探測邏輯（重複實作，非共用函式）。Mistral（SPM）產生的候選字串會帶有 `d r a g o n` 形式的空格，必須在比對 crack rate 前去除；Qwen（tiktoken）則不需要這道後處理。`util/search.py` 的搜尋演算法本身對兩種 tokenizer 完全透明，不含任何 model-aware 分支。

---

## 4. 模型載入與量化 — `lora_kind`

檔案：[util/train.py:34-60](../util/train.py)、[config/train_config.yaml](../config/train_config.yaml)

```yaml
# LoRA 種類：lora（標準 bf16 LoRA）或 qlora（4-bit 量化，適用 7B+ 模型）
lora_kind: lora
```

模型載入邏輯本身不分 Qwen/Mistral，只分 `lora_kind`：

- `qlora`：4-bit NF4 量化載入（`BitsAndBytesConfig` + `paged_adamw_8bit`），原為 12GB 顯卡跑 7B+ 模型的預設選擇。
- `lora`：標準 bf16 載入。

> 目前 `train_config.yaml` 設為 `lora_kind: lora`（非量化），用於 Mistral-7B-v0.1 run_6/run_7 — 在 12GB 卡上以標準 bf16 跑 7B 模型，搭配下方第 5 節的加大 LoRA rank。Qwen3-4B run_8 因模型較小，沒有量化壓力，同樣可用標準 LoRA。

---

## 5. LoRA rank / alpha — 已知未完整記錄的缺口

`config/train_config.yaml` 的 `lora_config` 預設值為 `r=16, lora_alpha=32`，且在整個 git 歷史中從未變更過。但實際訓練時 rank 可能被覆寫：

- **Mistral run_6 / run_7**：確認使用 `r=32, alpha=64`（雙倍於預設值），細節見 [comparison_run6_vs_run7 報告](reports/comparison_run6_vs_run7_Mistral-7B_id5_constrained_beam_search.md)。
- **Qwen3-4B run_8**：實際 r/alpha **未記錄**在 `id5_run8` 報告中，無法確認是否為預設值——這是 [Mistral vs Qwen 比較報告](reports/comparison_Mistral-7B_vs_Qwen3-4B_id5_constrained_beam_search.md)中標註的潛在混淆因子。

**根因：** `train_config.yaml` 只是訓練啟動時的設定檔快照，若訓練當下用 CLI override 或手動改過未提交的設定，git 歷史不會留下記錄。

**建議：** 每次訓練完成後，把實際生效的 `lora_config`（尤其 r/alpha）寫進對應 eval 報告的「實驗設定」表格，不要只依賴 `train_config.yaml` 的 git 歷史；或直接讀取 `checkpoints/{model}/run_N/lora_final/adapter_config.json`（peft 儲存的 adapter 設定檔，內含實際 r/alpha，是比訓練設定檔更可靠的 source of truth）。

---

## 6. Prompt Template — 完全 model-agnostic

`src/prompt_template.py` 純粹是文字模板組裝（JSON 結構 + tag 描述），不依賴 tokenizer，因此 Qwen 與 Mistral 可以共用完全相同的 template id（目前皆用 id=5，訓練 = 推論）。差異只發生在 tokenizer 把這些文字轉成 token ID 的階段（即上述第 2、3 節）。

---

## 相關檔案

- [util/pw_tokenize.py](../util/pw_tokenize.py) — `get_alpa()` 雙策略詞表建構
- [run_eval.py](../run_eval.py) — `_needs_space_strip` 推論後處理
- [util/train.py](../util/train.py) — `build_model_and_tokenizer()` / `apply_lora()`
- [config/train_config.yaml](../config/train_config.yaml) — `lora_kind` + `lora_config` 預設值
- [docs/logs/20260629_modify.md](logs/20260629_modify.md) — `get_alpa()` 偵測邏輯修正紀錄
- [docs/reports/comparison_run6_vs_run7_Mistral-7B_id5_constrained_beam_search.md](reports/comparison_run6_vs_run7_Mistral-7B_id5_constrained_beam_search.md)
- [docs/reports/comparison_Mistral-7B_vs_Qwen3-4B_id5_constrained_beam_search.md](reports/comparison_Mistral-7B_vs_Qwen3-4B_id5_constrained_beam_search.md)
