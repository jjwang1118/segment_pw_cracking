# LLM PCFG Cracking Model

## Project Overview

Password guessing/cracking research system that combines three techniques:

1. **PwdSegment BPE Tokenization** — segment passwords into semantically meaningful sub-tokens using custom Byte-Pair Encoding
2. **PCFG Semantic Tagging** — label tokens with linguistic/structural tags via `semantic-guesser` library
3. **LLM Fine-tuning** — fine-tune Llama-3.2-3B-Instruct with LoRA to generate targeted password candidates

The model learns that a password with structure `(fname)(number2)(special1)` (e.g., `alice99!`) follows a common naming pattern, enabling guided generation.

**Datasets:** 000webhost (~567K cleaned), phpbb (~96K), hotmail (~6K)
**Base Model:** `models/Llama-3.2-3B-Instruct` (3B params, instruction-tuned)
**Hardware:** RTX 5070 12GB, bfloat16

---

## 5-Stage Pipeline

```
Raw passwords (datasets/*.txt)
        ↓
[1] processData.py          → datasets/cleaned/{dataset}/cleaned_data.txt
        ↓
[2] trainBPE.py             → models/tokenizer/{dataset}/
        ↓
[3] run_tokenize.py         → gen/tokenized/ + gen/tagged/
        ↓
[4] util/Dataprocess.py     → datasets/processed/split/train_data.jsonl
        ↓
[5] run_train.py            → checkpoints/Llama-3.2-3B-Instruct/
```

### Stage 1: Password Cleaning (`processData.py`)

- Filters by length (8–20), character sets (lower/upper/digit/special), ASCII validity
- Removes duplicates and all-same-character passwords
- Config: `config/config.yaml` → `password_cleaning` section
- Input: `datasets/{dataset}.txt` | Output: `datasets/cleaned/{dataset}/cleaned_data.txt`

### Stage 2: BPE Tokenizer Training (`trainBPE.py`)

- Trains a custom BPE tokenizer on the cleaned corpus
- Two modes (controlled by `config.yaml` → `bpe.avg_len`):
  - **Standard mode** (`avg_len: null`): HuggingFace `BpeTrainer`, stops at `vocab_size`
  - **PwdSegment mode** (`avg_len: 4.5` or `1.8`): custom loop that stops when average token length ≥ threshold
- Output: `models/tokenizer/{dataset}/tokenizer.json`, `vocab_freq.json`, `vocab_with_freq.json`, `merged_vocab.json`

**Segmentation examples (avg_len=4.5):**
- `dragon99!` → `['dragon', '99', '!']`
- `password123` → `['password', '123']`

### Stage 3: PCFG Tagging (`run_tokenize.py`)

- Encodes each password with the BPE tokenizer, then tags each token via `semantic-guesser`
- Requires `models/semantic-guesser/` to be present (external library)
- Three tagging modes (`config/tokenize_setting.yaml` → `tagging.tagtype`):
  - `pos` — CLAWS7 POS tags: `nn`, `vv0`, `np`, `jj`, etc.
  - `backoff` — structural fallback: `char3`, `number2`, `special1`, `mixed4`
  - `pos_semantic` — WordNet synsets: `s.love.v.01`, `nn_unk`
- Output:
  - `gen/tokenized/{dataset}_tokenized.csv` — `Password | Tokens`
  - `gen/tagged/{dataset}_{tagtype}_tagged.csv` — `Password | Tokens | Tags | Structure`

**Example:** `dragon99!` → tokens `dragon|99|!` → tags `nn|number2|special1` → structure `(nn)(number2)(special1)`

### Stage 4: Dataset Splitting (`util/Dataprocess.py`)

- Loads all tagged CSVs, re-filters by length, samples by `expected_ratio`, splits train/test
- Output: `datasets/processed/split/train_data.jsonl`, `test_data.jsonl`, `length_distribution.json`
- Config: `config/train_config.yaml` → `expected_ratio`, `split_ratio`

**JSONL sample format:**
```json
{"Password": "kokak0l1", "Tokens": "kok|ak|0|l1", "Tags": "char3|char2|number1|mixed2", "source": "000webhost"}
```

### Stage 5: LLM Fine-tuning (`run_train.py`)

- Loads Llama-3.2-3B-Instruct and wraps with LoRA via PEFT
- For each training sample, constructs:
  - System prompt (targeted guessing instruction)
  - Knowledge JSON: `{token: tag_explanation}` pairs from `pcfg_tags.py`
  - Password: **character-by-character encoded** (95 printable ASCII chars mapped to token IDs, NOT BPE)
- Loss computed only on password tokens; prompt + knowledge are masked with `label=-100`
- Config: `config/train_config.yaml` → `train` section

---

## Directory Layout

```
llm_pcfg_cracking model/
├── config/
│   ├── config.yaml               # BPE training + password cleaning + wordcloud
│   ├── tokenize_setting.yaml     # Tokenizer inference + PCFG tagging settings
│   ├── train_config.yaml         # LLM training hyperparams + LoRA config
│   └── search.yaml               # Contrastive search params + eval settings
├── src/
│   ├── BPE.py                    # BPE tokenizer training (Standard + PwdSegment)
│   ├── Tokenize.py               # BPE inference + PCFG tag pipeline
│   ├── prompt_template.py        # LLM prompt templates for password guessing
│   └── datasets.py               # (placeholder)
├── util/
│   ├── data.py                   # Password loading, cleaning, deduplication
│   ├── trainTokenizer.py         # Tokenizer training dispatcher
│   ├── cloud.py                  # WordCloud visualization
│   ├── Dataprocess.py            # JSONL splitting + length distribution
│   ├── pw_tokenize.py            # Char-level encoding + batch preprocessing for training
│   ├── train.py                  # LLM training orchestration (load model, LoRA, Trainer)
│   ├── search.py                 # Inference: password generation via contrastive search
│   └── analyze.py                # Token analysis (Zipf's law, cross-dataset stats)
├── datasets/
│   ├── *.txt                     # Raw password files (one per line)
│   ├── cleaned/{dataset}/        # After Stage 1
│   └── processed/split/          # After Stage 4 (JSONL)
├── models/
│   ├── tokenizer/{dataset}/      # BPE tokenizer outputs per dataset
│   ├── semantic-guesser/         # External PCFG tagger (must be present for Stage 3)
│   └── Llama-3.2-3B-Instruct/   # Base LLM weights
├── checkpoints/
│   └── Llama-3.2-3B-Instruct/   # LoRA checkpoint directories + TensorBoard runs
├── gen/
│   ├── tokenized/                # CSV output of Stage 3 tokenization
│   ├── tagged/                   # CSV output of Stage 3 tagging (3 tag types × 3 datasets)
│   ├── cloud/                    # WordCloud PNGs of token frequency
│   └── analysis/                 # Zipf law plots, cross-dataset token overlap
├── docs/
│   ├── pipeline.md               # Complete pipeline explanation (Chinese)
│   ├── BPE_in_PwdSegment.md      # PwdSegment algorithm details
│   ├── LLM_Integration_Strategy.md
│   ├── BPE_Tokenizer_Analysis_Report.md
│   └── logs/                     # Development logs
├── results/                      # Legacy analysis outputs
├── processData.py                # Entry point: Stage 1
├── trainBPE.py                   # Entry point: Stage 2
├── run_tokenize.py               # Entry point: Stage 3
├── run_train.py                  # Entry point: Stage 5
├── run_search.py                 # Entry point: Password generation (contrastive search, no eval)
├── run_eval.py                   # Entry point: Evaluation (structure → candidates → crack rate)
└── pcfg_tags.py                  # PCFG tag definitions + get_explanation()
```

---

## Configuration Files

### `config/config.yaml` — BPE & Cleaning

```yaml
bpe:
  vocab_size: 4096          # Max vocabulary size
  avg_len: 4.5              # PwdSegment stop threshold (null = standard HF BpeTrainer)
  min_frequency: 1
  train: true               # Set false to skip retraining
  sampling_size: 100000     # Max passwords sampled for training

password_cleaning:
  dataset: ['000webhost']   # Datasets to process
  min_length: 8 / max_length: 20
  allowed_charsets: {lowercase, uppercase, digits, special}
  reject_non_ascii: true
  dedup: true

cloud:
  top_k: 3000              # Top tokens shown in word cloud
```

### `config/tokenize_setting.yaml` — PCFG Tagging

```yaml
tokenize:
  dataset: '000webhost'
  dirs:
    datasets: 'datasets'
    tokenizer: 'models/tokenizer'
    tokenized: 'gen/tokenized'
    tagged: 'gen/tagged'
  tagging:
    semantic_guesser_path: 'models/semantic-guesser'
    tagtype: 'pos'          # pos | backoff | pos_semantic
```

### `config/train_config.yaml` — LLM Training

```yaml
seed: 42
segment_tag_path:
  kind: backoff             # Must match tagged CSV type used in Stage 3
  dataset: [hotmail, phpbb, 000webhost]
expected_ratio: 0.4         # Fraction of data to sample
split_ratio: 0.2            # Test set fraction

train:
  prompt_template_id: 1
  train_config:
    model_name: Llama-3.2-3B-Instruct
    model_path: models
    output_dir: checkpoints/
    per_device_train_batch_size: 4
    gradient_accumulation_steps: 64  # Effective batch = 256
    learning_rate: "5e-4"
    num_train_epochs: 3
    warmup_ratio: 0.1
    eval_steps: 100
    save_steps: 200
    bf16: true

  lora_config:
    r: 16
    target_modules: [q_proj, k_proj, v_proj]
    lora_alpha: 32
    lora_dropout: 0.2
```

---

## Key Source Files

| File | Purpose |
|------|---------|
| `src/BPE.py` | `BPE(config)` creates HF tokenizer; `_train_with_avg_len()` implements PwdSegment loop |
| `src/Tokenize.py` | `Tokenizer_tag` class: `tokenize()` runs BPE, `tag()` calls semantic-guesser |
| `util/data.py` | `load_data()`, `clean_data()`, `remove_duplicates()`, `save_cleaned_data()` |
| `util/pw_tokenize.py` | `get_alpa(tokenizer)` maps 95 printable chars to token IDs; `process_train_targeted()` builds training batches with label masking |
| `util/train.py` | `build_model_and_tokenizer()`, `apply_lora()`, `train()` orchestrates HF Trainer |
| `util/Dataprocess.py` | `load_tagged_data()`, `sample_data()`, `split_train_test()` → writes JSONL |
| `util/search.py` | Contrastive search inference with custom 95-char vocabulary remapping |
| `run_eval.py` | Evaluation entry point: reads test JSONL, runs per-password contrastive search, outputs crack metrics |
| `run_search.py` | Generation-only entry point: contrastive search without ground-truth evaluation |
| `pcfg_tags.py` | `get_explanation(tag)` — pattern-based lookup for all tag types |
| `src/prompt_template.py` | `prompt_convert_token_tag()` (id=1): token+tag prompt; `prompt_convert_structure_only()` (id=2): structure-only prompt; `get_prompt_template(id)` |

---

## PCFG Tag Types

| Tag Category | Examples | Description |
|---|---|---|
| Structural (backoff) | `number2`, `char4`, `special1`, `mixed3` | Length-typed character class |
| POS (CLAWS7) | `nn`, `vv0`, `np`, `jj`, `vvd` | Part-of-speech |
| Semantic (proper nouns) | `fname`, `mname`, `surname`, `city`, `country` | Named entity type |
| WordNet synsets | `s.love.v.01`, `s.fire.n.02` | Word sense |
| Combined | `nn_unk`, `pos_synset` | POS + semantic combined |

---

## LLM Training Details

**Prompt structure per training sample (id=1 `prompt_convert_token_tag`):**
```
[System]: As a targeted password guessing model, your task is to generate likely
          password candidates based on the structural pattern and segment information...
[User]: {"This password can be segmented and tag into the following part":
           [["dragon","nn"],["99","number2"],["!","special1"]],
         "For each segment, each tag represents the following meaning":
           {"nn": "...", "number2": "...", "special1": "..."}}
[Assistant]: d r a g o n 9 9 !   ← only these tokens produce loss
```

**Character encoding:** `util/pw_tokenize.py:get_alpa()` maps each of 95 printable ASCII characters to its Llama tokenizer ID, enabling character-level control during generation.

**LoRA:** Only `q_proj`, `k_proj`, `v_proj` are trained (~0.1–1% of parameters). Checkpoints store `adapter_config.json` + `adapter_weights.safetensors` (not full model weights).

---

## Evaluation Methodology

The evaluation simulates a **targeted password guessing** attack: given a password's structural fingerprint (Tokens + Tags, already computed in Stage 3), can the model reconstruct the actual password without being shown it?

**Key insight:** Structural tags are derived from the password's content but do not directly encode it. Providing tokens + tags to the model at inference time mirrors a real-world scenario where an attacker knows something about a target password's structure (e.g., from social engineering or leaked hints) but not the actual characters.

### Two Inference Modes

| `prompt_template_id` | What the model receives | Use case |
|---|---|---|
| `1` | system_prompt + `{token: tag_explanation}` pairs (actual token strings as keys) | Fair test — matches training format |
| `2` | system_prompt + `{"password structure": "(tag1)(tag2)...", "segment details": {"position N": explanation}}` | Generalization test — no token strings given |

**id=1 prompt example** (Password: `indianglaze1`):
```
As a targeted password guessing model...
{"This password can be segmented and tag into the following part":
  [["in","ii"],["di","char2"],["ang","char3"],["laz","char3"],["e1","mixed2"]],
 "For each segment, each tag represents the following meaning":
  {"ii": "preposition or conjunction", "char2": "2-character alphabetic string", ...}}
```

**id=2 prompt example** (same password, structure-only):
```
As a targeted password guessing model... Each segment describes only the character class...
{"password structure": "(ii)(char2)(char3)(char3)(mixed2)",
 "segment details": {"position 1": "preposition or conjunction (ii)",
                     "position 2": "2-character alphabetic string (char2)", ...}}
```

### Evaluation Flow (`run_eval.py`)

```
For each entry in test_data.jsonl:

  {Password: "indianglaze1", Tokens: "in|di|ang|laz|e1", Tags: "ii|char2|char3|char3|mixed2"}
                                      ↓
      _build_prompt(entry, template_id)  [real password NEVER given to model]
                                      ↓
      input_ids = tokenize(full_prompt)
                                      ↓
      candidates = contrastive_search(model, input_ids)
      → up to 1000 candidate passwords, sorted by probability descending
                                      ↓
      if real_password in candidates:
          min_cracked_guess_number = rank  (1-indexed)
      else:
          min_cracked_guess_number = 0    (not cracked)
```

### Metrics

| Metric | Description |
|--------|-------------|
| `min_cracked_guess_number` | Rank of real password in candidate list; 0 = not cracked |
| **Crack rate @ K** | Fraction of test passwords cracked within top-K candidates (K = 1, 10, 100, 1000) |

### Output Format (`gen/eval_results.jsonl`)

```json
{
  "index": 0,
  "real_password": "indianglaze1",
  "tokens": "in|di|ang|laz|e1",
  "tags": "ii|char2|char3|char3|mixed2",
  "source": "000webhost",
  "model_input": "<full prompt text>",
  "candidates": [["indiana123", 0.85], ["indiaglaze1", 0.72], ...],
  "min_cracked_guess_number": 3
}
```

### Configuration (`config/search.yaml`)

Search parameters read from `contrastive_search` section; eval-specific fields in `eval` section:

```yaml
contrastive_search:
  prompt_template_id: 1      # 1 = with token strings, 2 = structure-only
  beam_width: [95, 1000×15]
  max_guess_number: 1000
  min_len: 8
  # ... other search params

eval:
  test_data_path: datasets/processed/split/test_data.jsonl
  max_eval_samples: 500      # Subset size (full 53K is impractical per-run)
  eval_output_file_name: eval_results.jsonl
  model_path: checkpoints/Llama-3.2-3B-Instruct/run_2/lora_final  # optional
```

**LoRA auto-detection**: if `model_path` contains `adapter_config.json`, `_load_model()` automatically loads via PEFT and calls `merge_and_unload()` for faster inference.

---

## Dependencies

```
torch, transformers, datasets, peft    # Core ML stack
tokenizers                              # HuggingFace tokenizer library
pandas, numpy                           # Data processing
pyyaml                                  # Config loading
wordcloud, matplotlib                   # Visualization
```

External (must be cloned/linked manually):
- `models/semantic-guesser/` — PCFG tagger with `BackoffTagger` and `GrammarTagger` classes; required for Stage 3

---

## Current Training Status (2026-06-07)

- **run_1** (廢棄): `checkpoints/Llama-3.2-3B-Instruct/checkpoint-2517`, prompt `id=0` — prompt template 與實際訓練格式不一致，已廢棄重訓
- **run_5 → run_2** (current): checkpoints 目前存於 `checkpoints/Llama-3.2-3B-Instruct/run_5/`（訓練進行中），最終將輸出至 `run_2/lora_final`，prompt `id=1`, tag type `backoff` — 以 backoff 結構標籤重新訓練，為目前主線版本
- Training runs at ~200 steps/3h on RTX 5070
- Recent optimizations in `docs/logs/20260606_modify.md`:
  - `enable_input_require_grads()` for gradient_checkpointing + LoRA compatibility
  - Removed `load_best_model_at_end` (incompatible with masked labels)
  - `TOKENIZERS_PARALLELISM=false` to suppress fork warnings
  - `<`, `|`, `>` excluded from inference vocab to prevent `<|special|>` token artifacts
  - `min_len` guard in contrastive beam search to prevent short outputs
  - Auto-increment `run_N` directory structure for checkpoints

## Future Work

- **run_3** (planned): fine-tune with `pos` tag type (CLAWS7 POS tags: `nn`, `vv0`, `np`, etc.) — validate whether linguistic POS information improves crack rate vs `backoff` baseline
- **run_4** (planned): fine-tune with `pos_semantic` tag type (WordNet synsets: `s.love.v.01`, etc.) — test high-semantic-content tagging for targeted cracking
- Target experiment: compare Crack rate @ K across `backoff` / `pos` / `pos_semantic` on the same test set to quantify the relationship between tag semantic richness and crack rate
