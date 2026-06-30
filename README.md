# LLM PCFG Cracking Model

## 專案目標

以 LLM 結合 PCFG 結構標籤，進行**定向密碼猜測（targeted password guessing）**。

核心假設：攻擊者已知目標密碼的結構特徵（如「名詞＋2位數字＋1個符號」），但不知道實際字元。透過 PCFG 對密碼做結構標注，再微調 LLM，使模型能從結構描述生成符合該分佈的候選密碼。


---

## Pipelines

### Pipeline A — BPE（legacy，baseline 對照用）

```
processData.py → trainBPE.py → run_tokenize.py → util/Dataprocess.py → run_train.py
```

BPE 依語料頻率切分，`dragon99!` → `drag|on|99|!`，切分結果與 PCFG tag 語意不對齊，僅作為對照組。

### Pipeline B — PCFG-native（current）

```
processData.py → run_pcfg_segment.py → run_train.py
```

依字元類別邊界切分，`dragon99!` → `dragon|99|!`，與 PCFG tag 語意一致。`run_pcfg_segment.py` 同時完成切分、打標、train/test 分割。

### 執行指令

```bash
# Step 1：資料清洗（兩條 path 共用）
python processData.py

# Step 2：PCFG-native 切分 + 打標 + 分割（Pipeline B）
python run_pcfg_segment.py                    # 全部 tagtype × 全部 dataset
python run_pcfg_segment.py --tagtype backoff  # 單一 tagtype
python run_pcfg_segment.py --split-only       # CSV 已存在，只重做分割

# Step 3：LLM 微調
python run_train.py
python run_train.py --resume checkpoints/Qwen3-4B/run_N/checkpoint-XXX

# Step 4：評估 crack rate
python run_eval.py

# Step 4（無 ground-truth）：純生成
python run_search.py
```

**資料流（Pipeline B）：**
`datasets/*.txt` → `datasets/cleaned/{dataset}/` → `gen/semanticPCFG/{dataset}_{tagtype}_tagged.csv` → `datasets/processed/semanticPCFG/{tagtype}/split/{train,test}_data.jsonl`

---

## Prompt Templates

透過 `config/train_config.yaml` 的 `prompt_template_id` 切換訓練格式；推論格式由 `config/search.yaml` 中各 search method 的 `prompt_template_id` 控制。

範例密碼：`dragon99!`　Tokens: `dragon|99|!`　Tags: `nn|number2|special1`

| id | 函數名 | 描述呈現方式 | Assistant 輸出格式 | 狀態 |
|---|---|---|---|---|
| **3** | `prompt_convert_structure_placeholder` | `<SEG1>` + 自然語言說明（`get_explanation()`） | 空格分隔字元：`d r a g o n 9 9 !` | **current** |
| 4 | `prompt_convert_segment_newline` | `<SEG1>` + `tag — short description` | 每 segment 獨立一行，post-processing 拼接 | 測試中 |
| 5 | `prompt_convert_inline` | `<tag>` 直接作佔位符，無說明 | 空格分隔字元序列 | 測試中 |

所有 template 均不暴露真實 token 字串。Assistant 輸出逐字元空格分隔，對應 `get_alpa()` 95-char vocab mapping。

**id=3 User prompt 範例：**
```json
{"password structure": "(<SEG1>)(<SEG2>)(<SEG3>)",
 "segment details": {"<SEG1>": "A singular common noun.",
                     "<SEG2>": "A sequence of exactly 2 digit characters (0-9).",
                     "<SEG3>": "Exactly 1 non-alphanumeric special character."}}
```

詳見 [docs/promt.md](docs/promt.md)

---

## Search Algorithms

透過 `config/search.yaml` 的 `search_type` 切換，`run_search.py` 與 `run_eval.py` 均支援：

```yaml
search_type: contrastive_search   # or dynamic_beam_search
```

### Dynamic Beam Search

純機率 beam search，無懲罰項。每步從 95-char vocab 保留 `beam_width` 條最高機率路徑。Prompt KV cache 共用，密碼 KV cache 各 beam 獨立。適合 baseline 比較，速度較快。

詳見 [docs/dynamic_beam_search.md](docs/dynamic_beam_search.md)

### Contrastive Search

Beam Search + 對比懲罰，提升候選集多樣性：

```
score = (1 - α) × logP(token | context) − α × max_cos_sim(h_current, H_history)
```

`α`（`contrastive_alpha`，預設 0.6）控制懲罰強度；`H_history` 為該 beam 的歷史 hidden state。懲罰重複性路徑，使 top-K 候選涵蓋更大解空間。`use_contrastive: false` 可退化為純 beam search。

詳見 [docs/contrastive_search.md](docs/contrastive_search.md)

### Constrained Decoding（兩者皆可啟用）

對 `backoff` tag 施加硬性字元類別與長度約束，將 prompt 的 soft guidance 升級為 hard enforcement。詳見 [docs/constrained_decoding.md](docs/constrained_decoding.md)

---

## Tag Types

| tagtype | 範例 | 說明 |
|---|---|---|
| `backoff` | `number2`, `char4`, `special1`, `mixed3` | 字元類別 + 長度；100% 覆蓋率，訓練優先 |
| `pos` | `nn`, `vv0`, `np`, `jj` | CLAWS7 詞性標籤；非英文 token fallback 為 `char4` |
| `pos_semantic` | `fname`, `city`, `s.love.v.01` | 命名實體 + WordNet synset；tag 空間碎散，暫緩 |

---

## Dependencies

```bash
pip install torch transformers datasets peft tokenizers pandas numpy pyyaml wordcloud matplotlib
pip install wordsegment nltk
python -c "import nltk; nltk.download('wordnet')"
```

外部套件（需手動 clone）：`models/semantic-guesser/` — PCFG tagger，兩條 pipeline 都需要
