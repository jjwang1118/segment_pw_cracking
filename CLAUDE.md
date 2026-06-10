# LLM PCFG Cracking Model

## Project Overview

Password guessing/cracking research system that combines three techniques:

1. **Segmentation** — split passwords into semantically meaningful sub-tokens via two approaches:
   - **BPE (legacy)**: custom Byte-Pair Encoding (`trainBPE.py` → `run_tokenize.py`)
   - **PCFG-native (current)**: PCFG's own regex + `wordsegment` segmentation (`run_pcfg_segment.py`)
2. **PCFG Semantic Tagging** — label tokens with linguistic/structural tags via `semantic-guesser` library
3. **LLM Fine-tuning** — fine-tune Llama-3.2-3B-Instruct with LoRA to generate targeted password candidates

The model learns that a password with structure `(fname)(number2)(special1)` (e.g., `alice99!`) follows a common naming pattern, enabling guided generation.

**Why PCFG-native segmentation?** BPE splits by frequency (`drag|on|99|!`), which is arbitrary and misaligns with PCFG tag semantics. PCFG-native splits by character class + word boundary (`dragon|99|!`), ensuring each segment and its tag are structurally coherent.

**Datasets:** 000webhost (~567K cleaned), phpbb (~96K), hotmail (~6K)
**Base Model:** `models/Llama-3.2-3B-Instruct` (3B params, instruction-tuned)
**Hardware:** RTX 5070 12GB, bfloat16

---

## Pipelines

### Pipeline A — BPE Segmentation (legacy)

```
Raw passwords (datasets/*.txt)
        ↓
[1] processData.py          → datasets/cleaned/{dataset}/cleaned_data.txt
        ↓
[2] trainBPE.py             → models/tokenizer/{dataset}/
        ↓
[3] run_tokenize.py         → gen/tokenized/ + gen/tagged/
        ↓
[4] util/Dataprocess.py     → datasets/processed/{tagtype}/split/train_data.jsonl
        ↓
[5] run_train.py            → checkpoints/Llama-3.2-3B-Instruct/
```

### Pipeline B — PCFG-native Segmentation (current)

```
Raw passwords (datasets/*.txt)
        ↓
[1] processData.py          → datasets/cleaned/{dataset}/cleaned_data.txt
        ↓
[2] run_pcfg_segment.py     → gen/semanticPCFG/{dataset}_{tagtype}_tagged.csv
             (Stage A: PCFG segment + tag)    datasets/processed/semanticPCFG/{tagtype}/split/
        ↓                   (Stage B: sample + train/test split)
[3] run_train.py            → checkpoints/Llama-3.2-3B-Instruct/
```

Pipeline B replaces Steps 2–4 with a single script. No BPE tokenizer is needed.

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

### Stage 3: PCFG Tagging — BPE path (`run_tokenize.py`)

- Encodes each password with the BPE tokenizer, then tags each token via `semantic-guesser`
- Requires `models/semantic-guesser/` to be present (external library)
- Three tagging modes (`config/tokenize_setting.yaml` → `tagging.tagtype`):
  - `pos` — CLAWS7 POS tags: `nn`, `vv0`, `np`, `jj`, etc.
  - `backoff` — structural fallback: `char3`, `number2`, `special1`, `mixed4`
  - `pos_semantic` — WordNet synsets: `s.love.v.01`, `nn_unk`
- Output:
  - `gen/tokenized/{dataset}_tokenized.csv` — `Password | Tokens`
  - `gen/tagged/{dataset}_{tagtype}_tagged.csv` — `Password | Tokens | Tags`

**Example (BPE):** `dragon99!` → BPE tokens `drag|on|99|!` → tags `char4|char2|number2|special1`

### Stage 3 (alt): PCFG-native Segmentation + Tagging (`run_pcfg_segment.py`)

- Uses PCFG's own regex + `wordsegment` to split, then tags via `semantic-guesser` — no BPE needed
- Config: `config/pcfg_segment.yaml`
- Three tagtypes: `pos` / `backoff` / `pos_semantic` (same as BPE path)
- Output:
  - `gen/semanticPCFG/{dataset}_{tagtype}_tagged.csv` — `Password | Tokens | Tags`
  - `datasets/processed/semanticPCFG/{tagtype}/split/train_data.jsonl`
  - `datasets/processed/semanticPCFG/{tagtype}/split/test_data.jsonl`

**Example (PCFG-native):** `dragon99!` → PCFG tokens `dragon|99|!` → tags `nn|number2|special1`

### Stage 4: Dataset Splitting — BPE path (`util/Dataprocess.py`)

- Loads all BPE-tagged CSVs, re-filters by length, samples by `expected_ratio`, splits train/test
- Output: `datasets/processed/{tagtype}/split/train_data.jsonl`, `test_data.jsonl`, `length_distribution.json`
- Config: `config/train_config.yaml` → `expected_ratio`, `split_ratio`
- **Note:** For PCFG-native path, Stage B of `run_pcfg_segment.py` replaces this step

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
│   ├── tokenize_setting.yaml     # Tokenizer inference + PCFG tagging settings (BPE path)
│   ├── pcfg_segment.yaml         # PCFG-native segmentation + tagging settings
│   ├── train_config.yaml         # LLM training hyperparams + LoRA config
│   └── search.yaml               # Contrastive search params + eval settings
├── src/
│   ├── BPE.py                    # BPE tokenizer training (Standard + PwdSegment)
│   ├── Tokenize.py               # BPE inference + PCFG tag pipeline
│   ├── PCFGSegment.py            # PCFG-native segmenter (PCFGSegmenter class)
│   ├── prompt_template.py        # LLM prompt templates for password guessing
│   └── datasets.py               # (placeholder)
├── util/
│   ├── data.py                   # Password loading, cleaning, deduplication
│   ├── trainTokenizer.py         # Tokenizer training dispatcher
│   ├── cloud.py                  # WordCloud visualization
│   ├── Dataprocess.py            # JSONL splitting + length distribution (BPE path)
│   ├── pw_tokenize.py            # Char-level encoding + batch preprocessing for training
│   ├── train.py                  # LLM training orchestration (load model, LoRA, Trainer)
│   ├── search.py                 # Inference: password generation via contrastive search
│   └── analyze.py                # Token analysis (Zipf's law, cross-dataset stats)
├── datasets/
│   ├── *.txt                     # Raw password files (one per line)
│   ├── cleaned/{dataset}/        # After Stage 1
│   ├── processed/{tagtype}/split/          # BPE path JSONL (after util/Dataprocess.py)
│   └── processed/semanticPCFG/{tagtype}/split/  # PCFG-native path JSONL
├── models/
│   ├── tokenizer/{dataset}/      # BPE tokenizer outputs per dataset
│   ├── semantic-guesser/         # External PCFG tagger (required for both paths)
│   └── Llama-3.2-3B-Instruct/   # Base LLM weights
├── checkpoints/
│   └── Llama-3.2-3B-Instruct/   # LoRA checkpoint directories + TensorBoard runs
├── gen/
│   ├── tokenized/                # CSV output of BPE tokenization
│   ├── tagged/                   # CSV output of BPE+PCFG tagging (3 tag types × 3 datasets)
│   ├── semanticPCFG/             # CSV output of PCFG-native tagging (3 tag types × 3 datasets)
│   ├── cloud/                    # WordCloud PNGs of token frequency
│   └── analysis/                 # Zipf law plots, cross-dataset token overlap
├── docs/
│   ├── pipeline.md               # Complete pipeline explanation (Chinese)
│   ├── BPE_in_PwdSegment.md      # PwdSegment algorithm details
│   ├── LLM_Integration_Strategy.md
│   ├── BPE_Tokenizer_Analysis_Report.md
│   └── logs/                     # Development logs
├── results/                      # Legacy analysis outputs
├── processData.py                # Entry point: Stage 1 (both paths)
├── trainBPE.py                   # Entry point: BPE training (BPE path only)
├── run_tokenize.py               # Entry point: BPE segmentation + PCFG tagging (BPE path)
├── run_pcfg_segment.py           # Entry point: PCFG-native segmentation + tagging + split
├── run_train.py                  # Entry point: LLM fine-tuning (both paths)
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

### `config/tokenize_setting.yaml` — BPE Path PCFG Tagging

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

### `config/pcfg_segment.yaml` — PCFG-native Path

```yaml
seed: 42
datasets: [000webhost, phpbb, hotmail]
tagtypes: [pos, backoff, pos_semantic]
semantic_guesser_path: models/semantic-guesser
dirs:
  datasets: datasets/cleaned          # {datasets}/{dataset}/cleaned_data.txt
  tagged:   gen/semanticPCFG          # {tagged}/{dataset}_{tagtype}_tagged.csv
  processed: datasets/processed/semanticPCFG  # {processed}/{tagtype}/split/
password_filter:
  min_length: 8
  max_length: 20
expected_ratio: 0.4
split_ratio: 0.2
force_retag: false
```

### `config/train_config.yaml` — LLM Training

```yaml
seed: 42
# BPE path:          dataset_path: datasets/processed/backoff
# PCFG-native path:  dataset_path: datasets/processed/semanticPCFG/backoff
dataset_path: datasets/processed/semanticPCFG/backoff
segment_tag_path:
  path: gen/semanticPCFG    # gen/tagged for BPE path; gen/semanticPCFG for PCFG-native
  kind: backoff             # pos | backoff | pos_semantic
  dataset: [hotmail, phpbb, 000webhost]
expected_ratio: 0.4         # Fraction of data to sample (BPE path only)
split_ratio: 0.2            # Test set fraction (BPE path only)

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
| `src/PCFGSegment.py` | `PCFGSegmenter(sg_path, tagtype)`: `segment_and_tag(pw)` → PCFG-native split + tag |
| `run_pcfg_segment.py` | Entry point for PCFG-native pipeline: Stage A (tag → CSV) + Stage B (split → JSONL) |
| `util/data.py` | `load_data()`, `clean_data()`, `remove_duplicates()`, `save_cleaned_data()` |
| `util/pw_tokenize.py` | `get_alpa(tokenizer)` maps 95 printable chars to token IDs; `process_train_targeted()` builds training batches with label masking |
| `util/train.py` | `build_model_and_tokenizer()`, `apply_lora()`, `train()` orchestrates HF Trainer |
| `util/Dataprocess.py` | `load_tagged_data()`, `sample_data()`, `split_train_test()` → writes JSONL |
| `util/search.py` | Two search algorithms: `dynamic_beam_search` (pure beam, no penalty) and `contrastive_search` (beam + contrastive penalty); shared KV-cache helpers (`_reorder_cache`, `_cache_concat`, etc.); custom 95-char vocab remapping |
| `run_eval.py` | Evaluation entry point: reads test JSONL, dispatches to `contrastive_search` or `dynamic_beam_search` based on `search_type`, outputs crack metrics |
| `run_search.py` | Generation-only entry point: supports `contrastive_search` and `dynamic_beam_search`; dispatcher pattern via `_DISPATCHERS` / `_CANONICAL_NAMES` |
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
      candidates = contrastive_search(model, input_ids)   # or dynamic_beam_search
      → up to 1000 candidate passwords, sorted by probability descending
      (search method selected by search_type in config/search.yaml)
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

Top-level `search_type` key selects which method both `run_search.py` and `run_eval.py` use. Each method has its own config section:

```yaml
search_type: contrastive_search  # or dynamic_beam_search

contrastive_search:
  prompt_template_id: 1      # 1 = with token strings, 2 = structure-only
  beam_width: [95, 1000×15]
  max_guess_number: 1000
  min_len: 8
  contrastive_alpha: 0.6     # penalty weight (contrastive_search only)
  use_contrastive: true      # set false to disable penalty (contrastive_search only)
  # ... other search params

dynamic_beam_search:
  prompt_template_id: 1
  beam_width: [95, 1000×15]
  max_guess_number: 1000
  min_len: 8
  # no contrastive params — pure probability beam search

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
- `models/semantic-guesser/` — PCFG tagger with `BackoffTagger` and `GrammarTagger` classes; required for both BPE path (Stage 3) and PCFG-native path

Extra dependency for PCFG-native path:
```
wordsegment                             # Word boundary detection within alpha runs
nltk (wordnet corpus)                   # Required for pos_semantic tagtype
```

---

## Current Training Status (2026-06-11)

- **run_1** (廢棄): `checkpoints/Llama-3.2-3B-Instruct/checkpoint-2517`, prompt `id=0` — prompt template 與實際訓練格式不一致，已廢棄重訓
- **run_5 → run_2** (進行中 / baseline): checkpoints 存於 `checkpoints/Llama-3.2-3B-Instruct/run_5/`，最終輸出至 `run_2/lora_final`，prompt `id=1`, tag type `backoff`，使用 **BPE 切分** — 作為 trawling-style baseline（BPE 切分語意弱，作為對照組）
- Training runs at ~200 steps/3h on RTX 5070
- Recent optimizations in `docs/logs/20260606_modify.md`:
  - `enable_input_require_grads()` for gradient_checkpointing + LoRA compatibility
  - Removed `load_best_model_at_end` (incompatible with masked labels)
  - `TOKENIZERS_PARALLELISM=false` to suppress fork warnings
  - `<`, `|`, `>` excluded from inference vocab to prevent `<|special|>` token artifacts
  - `min_len` guard in contrastive beam search to prevent short outputs
  - Auto-increment `run_N` directory structure for checkpoints
- 2026-06-08: Added `dynamic_beam_search` as a second inference method (`util/search.py`); `run_search.py` and `run_eval.py` now dispatch based on `search_type` in `config/search.yaml`
- 2026-06-08: Added PCFG-native segmentation pipeline (`src/PCFGSegment.py`, `run_pcfg_segment.py`, `config/pcfg_segment.yaml`) — uses PCFG's own regex + `wordsegment` to split passwords, ensuring segment ↔ tag alignment; outputs to `gen/semanticPCFG/` and `datasets/processed/semanticPCFG/`
- 2026-06-11: All three tagtypes (backoff / pos / pos_semantic) fully tagged and split for PCFG-native pipeline; JSONL datasets ready under `datasets/processed/semanticPCFG/{tagtype}/split/`

## Architecture Decision Notes (2026-06-11)

**Targeted vs Trawling:**
The current architecture is optimized for **targeted** password guessing, not trawling. The inference pipeline requires tokens + tags as input (structural fingerprint), which presupposes attacker knowledge of the target's password structure. Pure PCFG probability enumeration remains more efficient for trawling. LLM value is in learning contextual associations between segments (e.g., `fname` + `nn` → likely followed by `number2`), which is most meaningful in targeted scenarios.

**PCFG-native vs BPE:**
PCFG-native segmentation is structurally superior for this task. BPE splits by corpus frequency (`drag|on|99|!`), misaligning segments with their PCFG tags and forcing the LLM to learn arbitrary sub-string → tag mappings. PCFG-native splits by character-class boundary (`dragon|99|!`), ensuring each segment and its tag are coherent — the model learns linguistically meaningful structure → lexical generation mappings.

**Tag type priority: backoff > pos > pos_semantic**
- `backoff`: 100% coverage, zero noise, character-class typed (`char4`, `number2`, `special1`). Best signal-to-noise ratio for training.
- `pos`: CLAWS7 POS tags add linguistic structure for real English words (`nn`, `vv0`); non-English tokens fall back to `char4`. Worth testing after backoff baseline is established.
- `pos_semantic`: WordNet synsets + named entity tags (`fname`, `city`) are theoretically the richest for targeted attacks, but tag space is highly fragmented (many rare tags, low sample counts), knowledge JSON grows large, and coverage degrades for non-dictionary tokens. Defer until pos shows clear benefit.

