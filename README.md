# LLM PCFG Cracking Model

A password cracking model combining Large Language Models (LLM) with Probabilistic Context-Free Grammar (PCFG), featuring a BPE tokenizer trained specifically on password datasets.

## Project Structure

```
├── config.yaml          # Central configuration file
├── processData.py       # Password dataset cleaning & preprocessing
├── trainBPE.py          # BPE tokenizer training entry point
├── src/
│   └── BPE.py           # BPE model builder (standard + PwdSegment modes)
├── util/
│   ├── data.py          # Data loading, cleaning, deduplication utilities
│   ├── trainTokenizer.py# Tokenizer training dispatcher
│   └── cloud.py         # Word cloud visualization from vocab frequencies
├── datasets/            # Raw password datasets (.txt, one password per line)
├── models/tokenizer/    # Trained tokenizer outputs
└── results/             # Generated figures (word clouds, etc.)
```

## Workflow

### 1. Preprocess Data
Clean and deduplicate raw password datasets:
```bash
python processData.py
```
Output: `datasets/cleaned/cleaned_data.txt`

### 2. Train BPE Tokenizer
```bash
python trainBPE.py
```
Output files in `models/tokenizer/<dataset>/`:
| File | Description |
|---|---|
| `tokenizer.json` | HuggingFace tokenizer (vocab + merge rules) |
| `vocab_freq.json` | All tokens with frequencies |
| `vocab_with_freq.json` | All tokens with id + frequency, sorted by freq |
| `merged_vocab.json` | Merged tokens only (length ≥ 2), sorted by freq |

### 3. Visualize Vocabulary
```bash
python util/cloud.py
```
Output: `results/wordcloud.png`

## BPE Modes

| Mode | Config | Description |
|---|---|---|
| Standard | `avg_len: null` | HuggingFace BpeTrainer, stops at `vocab_size` |
| PwdSegment | `avg_len: 1.8` | Fine-grained, for CKL_Backoff / CKL_FLA |
| PwdSegment | `avg_len: 4.5` | Coarse-grained, for CKL_PCFG |

## Configuration

Key settings in `config.yaml`:

```yaml
bpe:
  vocab_size: 4096
  min_frequency: 2
  avg_len: null        # null = standard mode; 1.8 or 4.5 = PwdSegment mode
  train_corpus: "datasets/train"
  save_path: "models/tokenizer"

password_cleaning:
  dataset: ['000webhost', 'phpbb', 'hotmail']
  min_length: 8
  max_length: 20
  dedup: true
  output_path: "datasets/cleaned"
```

## References

- Ming Xu et al., *Password Cracking with PwdSegment*, CCS 2021
