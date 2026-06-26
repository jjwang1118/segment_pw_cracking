# LLM PCFG Cracking Model

## Project Overview

Password guessing/cracking research system: segment passwords → PCFG tag tokens → fine-tune Qwen3-4B (QLoRA) to generate targeted candidates.

- **Segmentation (current):** PCFG-native regex + `wordsegment` (`run_pcfg_segment.py`) — splits by character-class boundary (`dragon|99|!`), aligns with PCFG tag semantics
- **Segmentation (legacy):** BPE (`trainBPE.py` → `run_tokenize.py`) — splits by frequency (`drag|on|99|!`), misaligns with tags; kept as baseline
- **Tagging:** `semantic-guesser` library, 3 tag types: `backoff` (100% coverage) > `pos` (CLAWS7) > `pos_semantic` (WordNet)
- **Training:** Qwen3-4B, QLoRA (4-bit NF4 + `paged_adamw_8bit`), prompt id=3 (placeholder slots)
- **Datasets:** 000webhost (~567K), phpbb (~96K), hotmail (~6K)
- **Hardware:** RTX 5070 12GB

---

## Pipelines

### Pipeline A — BPE (legacy)
```
processData.py → trainBPE.py → run_tokenize.py → util/Dataprocess.py → run_train.py
               cleaned/       tokenizer/         gen/tagged/            checkpoints/
```

### Pipeline B — PCFG-native (current)
```
processData.py → run_pcfg_segment.py ──────────────────────────────── → run_train.py
               cleaned/       Stage A: gen/semanticPCFG/               checkpoints/
                               Stage B: datasets/processed/semanticPCFG/
```

**Data flow:** `datasets/*.txt` → `datasets/cleaned/{dataset}/cleaned_data.txt` → `gen/semanticPCFG/{dataset}_{tagtype}_tagged.csv` → `datasets/processed/semanticPCFG/{tagtype}/split/{train,test}_data.jsonl`

**JSONL format:**
```json
{"Password": "dragon99!", "Tokens": "dragon|99|!", "Tags": "nn|number2|special1", "source": "000webhost"}
```

---

## Directory Layout

```
llm_pcfg_cracking model/
├── config/
│   ├── config.yaml               # BPE training + password cleaning
│   ├── tokenize_setting.yaml     # BPE path tagging settings
│   ├── pcfg_segment.yaml         # PCFG-native segmentation settings
│   ├── train_config.yaml         # LLM training hyperparams + LoRA config
│   └── search.yaml               # search_type + eval settings
├── src/
│   ├── BPE.py                    # BPE tokenizer (Standard + PwdSegment modes)
│   ├── Tokenize.py               # BPE inference + PCFG tag pipeline
│   ├── PCFGSegment.py            # PCFGSegmenter: segment_and_tag(pw)
│   └── prompt_template.py        # Prompt templates (id=1/2/3)
├── util/
│   ├── data.py                   # load/clean/dedup passwords
│   ├── Dataprocess.py            # JSONL splitting (BPE path)
│   ├── pw_tokenize.py            # 95-char encoding + training batch builder
│   ├── train.py                  # build_model, apply_lora, HF Trainer orchestration
│   └── search.py                 # dynamic_beam_search + contrastive_search
├── datasets/cleaned/{dataset}/   # After processData.py
├── datasets/processed/semanticPCFG/{tagtype}/split/  # PCFG-native JSONL
├── models/
│   ├── semantic-guesser/         # External PCFG tagger (required, clone manually)
│   └── Qwen3-4B/                 # Base LLM weights
├── checkpoints/Qwen3-4B/         # QLoRA checkpoint dirs + TensorBoard
├── gen/
│   ├── tagged/                   # BPE path CSVs
│   └── semanticPCFG/             # PCFG-native path CSVs
├── processData.py                # Stage 1: cleaning (both paths)
├── trainBPE.py                   # BPE training (BPE path only)
├── run_tokenize.py               # BPE segmentation + tagging
├── run_pcfg_segment.py           # PCFG-native seg + tag + split (Stage A+B)
├── run_train.py                  # LLM fine-tuning
├── run_search.py                 # Password generation (no eval)
├── run_eval.py                   # Evaluation: structure → candidates → crack rate
└── pcfg_tags.py                  # get_explanation(tag) for all tag types
```

---

## Key Source Files

| File | Key symbols |
|------|-------------|
| `src/PCFGSegment.py` | `PCFGSegmenter(sg_path, tagtype)` → `segment_and_tag(pw)` |
| `src/prompt_template.py` | `get_prompt_template(id)`, `prompt_convert_structure_placeholder()` (id=3, current) |
| `util/pw_tokenize.py` | `get_alpa(tokenizer)` — 95-char→token-ID map; `process_train_targeted()` — batch builder with label masking |
| `util/train.py` | `build_model_and_tokenizer()`, `apply_lora()`, `train()` |
| `util/search.py` | `dynamic_beam_search`, `contrastive_search`; shared KV-cache helpers; 95-char vocab remapping |
| `run_eval.py` | reads test JSONL → dispatches search → outputs `gen/eval_results.jsonl` |
| `run_search.py` | `_DISPATCHERS` / `_CANONICAL_NAMES` dispatcher pattern |
| `pcfg_tags.py` | `get_explanation(tag)` pattern-based lookup |

---

## Prompt & Tags

**Prompt (id=3, current):** placeholder slots `<SEG1>…<SEGN>` + natural-language descriptions; raw tag strings never exposed; assistant outputs space-separated chars (`d r a g o n 9 9 !`); loss on assistant tokens only. `<`, `|`, `>` excluded from inference vocab. → see [docs/promt.md](docs/promt.md)

**Tag types:** `backoff` (structural, 100% coverage) / `pos` (CLAWS7 POS) / `pos_semantic` (WordNet synsets + named entities). Tag description rules (why examples were removed from descriptions) → see [docs/tag_description_modify.md](docs/tag_description_modify.md)

---

## Evaluation

Simulates targeted guessing: given Tags only (no characters), can the model reconstruct the password?

**Flow:** test JSONL → `_build_prompt()` → search → up to 1000 ranked candidates → `min_cracked_guess_number` (0 = not cracked)

**Metrics:** crack rate @ K (K = 1, 10, 100, 1000)

**Output:** `gen/eval_results.jsonl` — index, real_password, tokens, tags, candidates, min_cracked_guess_number

**Config:** `config/search.yaml` — top-level `search_type: contrastive_search | dynamic_beam_search`; LoRA auto-detected via `adapter_config.json`

Search algorithm details → [docs/contrastive_search.md](docs/contrastive_search.md) · [docs/dynamic_beam_search.md](docs/dynamic_beam_search.md) · [docs/constrained_decoding.md](docs/constrained_decoding.md)

---

## Dependencies

```
torch, transformers, datasets, peft, tokenizers   # ML stack
pandas, numpy, pyyaml                             # Data + config
wordsegment                                       # PCFG-native path
nltk (wordnet corpus)                             # pos_semantic tagtype
```

External: `models/semantic-guesser/` — clone manually; required for both pipelines.

---

## Reports & Results

### Raw Eval Log
- **Location:** `results/`
- **Naming:** `eval-{job_id}.out` (e.g. `results/eval-245621.out`) — stdout captured from HPC job
- **Contents:** per-password search trace (layer/beam progress) + per-entry summary line + final crack rate block
- **Note:** source of truth for crack numbers; processed results (JSONL, charts, reports) are derived from this file and stored under `gen/` and `docs/reports/`

### Processed Results
- **Location:** `gen/`
  - `gen/eval_results_*.jsonl` — per-entry JSONL output from `run_eval.py`
  - `gen/results/` — result charts (`.png`)

### Eval Report
- **Location:** `docs/reports/`
- **Naming:** `{model}_{N}B_id{template_id}_{search_kind}.md`
  - `{model}_{N}B` — model name, e.g. `Qwen3-4B`
  - `id{template_id}` — prompt template id, e.g. `id4`
  - `{search_kind}` — search method key from `search.yaml`, e.g. `constrained_beam_search`
  - Example: `docs/reports/Qwen3-4B_id4_constrained_beam_search.md`
- **Contents:** model + LoRA path, template id, eval count, max_guess, search method, crack rate @K table, tag type breakdown (backoff vs pos/pos_semantic), full cracked password list with tags

### Result Charts
- **Location:** `gen/results/`
- **Naming:** `{model}_{N}B_id{template_id}_{search_kind}_result.png`
  - Same tokens as report, with `_result` suffix
  - Example: `gen/results/Qwen3-4B_id4_constrained_beam_search_result.png`
- **Contents:** left — crack rate line chart (@1/@10/@100/@1000); right — cracked password tag type distribution pie chart

---

## Development Rules

**Change log:** Any modification to code or config must be recorded in `docs/logs/YYYYMMDD_modify.md`. Append to today's log if it exists; create a new file if it does not.

**Git:** Always ask the user to confirm the commit message and branches before pushing. Never decide the message unilaterally.

