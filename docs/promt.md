
### prompt template

範例密碼：`dragon99!`　Tokens: `dragon|99|!`　Tags: `nn|number2|special1`

---

#### id=3 `prompt_convert_structure_placeholder`

使用 placeholder slot `<SEG1>…<SEGN>`，描述文字由 `get_explanation()` 產生（`N` 已替換為實際長度，如 `number2` → `"A sequence of exactly 2 digit characters (0-9)."`）。不暴露原始 tag 符號或 token 字串。

**Assistant 輸出格式**：空格分隔字元序列，如 `d r a g o n 9 9 !`

**訓練時**（User prompt + Assistant response，loss 只算 Assistant 部分）：

```
[User]
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. The structure is represented with placeholder slots, and each slot includes only natural-language constraints. Do not output placeholders. Generate only plausible password characters that satisfy all slot constraints.{"password structure": "(<SEG1>)(<SEG2>)(<SEG3>)", "segment details": {"<SEG1>": "A singular common noun.", "<SEG2>": "A sequence of exactly 2 digit characters (0-9).", "<SEG3>": "Exactly 1 non-alphanumeric special character (e.g., '!', '@', '#')."}}

[Assistant]
d r a g o n 9 9 !
```

**推論時**（只輸入 User prompt，model 自行生成 Assistant 部分）：

```
[User]
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. The structure is represented with placeholder slots, and each slot includes only natural-language constraints. Do not output placeholders. Generate only plausible password characters that satisfy all slot constraints.{"password structure": "(<SEG1>)(<SEG2>)(<SEG3>)", "segment details": {"<SEG1>": "A singular common noun.", "<SEG2>": "A sequence of exactly 2 digit characters (0-9).", "<SEG3>": "Exactly 1 non-alphanumeric special character (e.g., '!', '@', '#')."}}

[Assistant]
▶ model generates here
```

> 注意：id=3 的 User prompt 在訓練與推論時**完全相同**（prompt 中不含實際字元，只有 tag 描述），差異只在是否提供 Assistant 答案。

---

#### id=4 `prompt_convert_segment_newline`

與 id=3 相同結構，但描述文字改用 `expand_tag_description()` — 格式為 `tag — short description`（如 `number2 — 2-digit number`）。

**Assistant 輸出格式**：每個 segment 獨立一行，post-processing 剝離 `\n` 後拼接還原完整密碼。

**訓練時**：

```
[User]
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. Each slot specifies both the character class and the exact character count. Generate each segment on a separate line in the given order. Do not output placeholder names. Output only the characters satisfying each slot constraint.{"password structure": "(<SEG1>)(<SEG2>)(<SEG3>)", "segment details": {"<SEG1>": "nn — singular common noun", "<SEG2>": "number2 — 2-digit number", "<SEG3>": "special1 — 1 special character"}}

[Assistant]
dragon
99
!
```

**推論時**：

```
[User]
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. Each slot specifies both the character class and the exact character count. Generate each segment on a separate line in the given order. Do not output placeholder names. Output only the characters satisfying each slot constraint.{"password structure": "(<SEG1>)(<SEG2>)(<SEG3>)", "segment details": {"<SEG1>": "nn — singular common noun", "<SEG2>": "number2 — 2-digit number", "<SEG3>": "special1 — 1 special character"}}

[Assistant]
▶ model generates here (each segment on a new line, post-processed by stripping \n and concatenating)
```

> 注意：id=4 的 User prompt 在訓練與推論時同樣**完全相同**。

---

#### id=5 `prompt_convert_inline`

Tag 名稱直接作為佔位符，**不含** segment 文字、不含自然語言描述。格式為 `<tag>` 連續串接在單一 `password structure` 字串中。訓練與推論的 User prompt **完全相同**。

**訓練時 = 推論時**（User prompt 只有 tag 序列）：

```
[User]
As a targeted password guessing model, your task is to generate likely password candidates that match the given tag structure. Each <tag> placeholder names the character class for that segment. Do not output the tag placeholders. Generate only the password characters for each segment in order.{"password structure": "<nn><number2><special1>"}

[Assistant]
d r a g o n 9 9 !
```

**推論時**：

```
[User]
...{"password structure": "<nn><number2><special1>"}

[Assistant]
▶ model generates here
```

> 注意：id=5 訓練與推論 prompt 完全一致，消除了舊版訓練時含 token 字串、推論時不含的不對稱問題。

---

#### id=6 `prompt_convert_inline_plain`

與 id=5 使用**完全相同**的 tag 結構表示法（`<tag1><tag2>...` 直接串接），但拿掉 JSON 包裝 —— system prompt 後接一個字面換行 `\n`，再直接接 inline tag 字串。訓練與推論的 User prompt **完全相同**。

**訓練時 = 推論時**（User prompt 只有 tag 序列，無 JSON）：

```
[User]
As a targeted password guessing model, your task is to utilize the provided structure information to guess the corresponding password.
<nn><number2><special1>

[Assistant]
d r a g o n 9 9 !
```

**推論時**：

```
[User]
As a targeted password guessing model, your task is to utilize the provided structure information to guess the corresponding password.
<nn><number2><special1>

[Assistant]
▶ model generates here
```

> 注意：id=6 與 id=5 的 tag 結構完全相同，差異只在有沒有 JSON 包裝（`{"password structure": "..."}`）—— id=6 是更精簡的純文字版本，prompt token 數更少。

---

---

#### id=3b `prompt_convert_structure_placeholder_newline`

與 id=3 **完全相同的 user prompt**，唯一差異是 assistant 輸出改為每 segment 獨立一行（同 id=4）。目的是讓模型在自然語言描述下學習以 segment 邊界為單位生成，而不是逐字元空格序列。

**訓練時**：

```
[User]
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. The structure is represented with placeholder slots, and each slot includes only natural-language constraints. Do not output placeholders. Generate each segment on a separate line in the given order. Output only the characters satisfying each slot constraint.{"password structure": "(<SEG1>)(<SEG2>)(<SEG3>)", "segment details": {"<SEG1>": "A singular common noun.", "<SEG2>": "A sequence of exactly 2 digit characters (0-9).", "<SEG3>": "Exactly 1 non-alphanumeric special character (e.g., '!', '@', '#')."}}

[Assistant]
dragon
99
!
```

**推論時**：user prompt 與訓練完全相同；post-processing 剝離 `\n` 後拼接還原完整密碼。

---

#### id=4b `prompt_convert_no_tag_newline`

與 id=4 相同的輸出格式（每 segment 一行），但描述改用 `get_explanation()`（自然語言），**不暴露 raw tag 名稱**（如 `number2`、`nn`）。

**訓練時**：

```
[User]
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. The structure is represented with placeholder slots, and each slot includes natural-language descriptions of the character class and constraints. Generate each segment on a separate line in the given order. Do not output placeholder names. Output only the characters satisfying each slot constraint.{"password structure": "(<SEG1>)(<SEG2>)(<SEG3>)", "segment details": {"<SEG1>": "A singular common noun.", "<SEG2>": "A sequence of exactly 2 digit characters (0-9).", "<SEG3>": "Exactly 1 non-alphanumeric special character (e.g., '!', '@', '#')."}}

[Assistant]
dragon
99
!
```

**推論時**：同 3b，post-processing 剝離 `\n` 後拼接。

> **3b vs 4b 的差異**：user prompt 知識內容完全相同（都用 `get_explanation()`），差異只在 system text 的措辭：3b 強調「只含自然語言約束」（沿用 id=3 框架），4b 強調「自然語言描述字元類別與長度」（沿用 id=4 框架但移除 tag 名稱）。

---

#### id=3 / id=4 / id=5 / id=6 差異

| | id=3 | id=4 | id=5 | id=6 |
|---|---|---|---|---|
| 描述函數 | `get_explanation()`（N 已展開） | `expand_tag_description()` | 無描述 | 無描述 |
| Tag 呈現 | `<SEG1>` + 自然語言說明 | `<SEG1>` + `tag — short` | `<tag>` 直接作佔位符 | `<tag>` 直接作佔位符（同 id=5） |
| 包裝格式 | JSON | JSON | JSON | 純文字（`\n` + tag 序列，無 JSON） |
| Segment 內容 | 不包含（訓練推論 prompt 相同） | 不包含（訓練推論 prompt 相同） | 不包含（訓練推論 prompt 相同） | 不包含（訓練推論 prompt 相同） |
| Assistant 輸出 | 空格分隔字元序列 | 每 segment 獨立一行 | 空格分隔字元序列 | 空格分隔字元序列 |
| Post-processing | 無 | 剝離 `\n` token 後拼接 | 無 | 無 |

#### id=3b / id=4b 與其他模板的差異

| | id=3b | id=4b |
|---|---|---|
| 描述函數 | `get_explanation()`（同 id=3） | `get_explanation()`（同 id=3） |
| Tag 名稱暴露 | 無（同 id=3） | 無（同 id=3） |
| System text 風格 | id=3 + per-line 指示 | id=4 風格但措辭改為自然語言 |
| Assistant 輸出 | 每 segment 獨立一行（同 id=4） | 每 segment 獨立一行（同 id=4） |
| Post-processing | 剝離 `\n` token 後拼接 | 剝離 `\n` token 後拼接 |
| 與 id=3 差異 | assistant 輸出格式 | assistant 輸出格式 + system text |
| 與 id=4 差異 | 描述改自然語言（無 tag 名） | 描述改自然語言（無 tag 名） |


#### id=7 `Combine the sister password and the tag information`

在 id=5 的 `password structure`（inline `<tag>`）基礎上，加入 `sibling passwords`（同帳號歷史密碼，取前 5 筆，無則為空陣列 `[]`，此時等價於 id=5）。訓練與推論的 User prompt **完全相同**。

**訓練時**：

```
[User]
As a targeted password guessing model, your task is to generate likely password candidates that match the given password information. The password structure is represented as a sequence of <tag> placeholders, and sibling passwords, if any, are prior passwords from the same account. Do not output the tag placeholders. Generate only the password characters for each segment in order.{"password structure": "<nn><number2><special1>", "sibling passwords": ["dragon98$"]}

[Assistant]
d r a g o n 9 9 !
```

**推論時**：

```
[User]
...{"password structure": "<nn><number2><special1>", "sibling passwords": ["dragon98$"]}

[Assistant]
▶ model generates here
```

> 注意：id=7 的 User prompt 在訓練與推論時完全相同；`sibling passwords` 只取「同帳號、非目標密碼」的歷史密碼，不含目標密碼本身。

---

#### id=8 `prompt_convert_multi_structure`（multi-structcand）

把「讀法 A（結構 1-1 → 1-N）」prompt 化：沿用 id=7 的 **list 機制**，但 list 裡裝的不是 sibling 密碼，而是**同一個目標密碼的其他候選結構**。同一密碼分別以三種 tag-type 標記（`backoff` / `pos` / `pos_semantic`），切分完全相同、只有 tag 顆粒度不同，三者互補（例如 `backoff` 保留 `mname`/`surname`/`city`，`pos_semantic` 對專有名詞塌成 `np1_unk`）。

**System prompt = id=5，不變。** 主結構 `password structure` 用 **backoff**，另兩種 tag-type 進 `candidate structures`。訓練與推論的 User prompt **完全相同**。

以 `dragon99!` 為例，三種 tag-type 的 inline 結構：

| tag-type | inline 結構 | 角色 |
|---|---|---|
| backoff | `<dragon.n.01><number2><special1>` | 主（`password structure`） |
| pos | `<nn1><number2><special1>` | 候選 |
| pos_semantic | `<nn1_dragon.n.01><number2><special1>` | 候選 |

**訓練時**：

```
[User]
As a targeted password guessing model, your task is to generate likely password candidates that match the given tag structure. Each <tag> placeholder names the character class for that segment. Do not output the tag placeholders. Generate only the password characters for each segment in order.{"password structure": "<dragon.n.01><number2><special1>", "candidate structures": ["<nn1><number2><special1>", "<nn1_dragon.n.01><number2><special1>"]}

[Assistant]
d r a g o n 9 9 !
```

**推論時**：

```
[User]
As a targeted password guessing model, your task is to generate likely password candidates that match the given tag structure. Each <tag> placeholder names the character class for that segment. Do not output the tag placeholders. Generate only the password characters for each segment in order.{"password structure": "<dragon.n.01><number2><special1>", "candidate structures": ["<nn1><number2><special1>", "<nn1_dragon.n.01><number2><special1>"]}

[Assistant]
▶ model generates here
```

> **id=8 vs id=5**：system prompt 完全相同，唯一差別是 JSON 多帶 `candidate structures`——構成乾淨 ablation（唯一變數＝「有沒有多餵候選結構」）。
> **id=8 vs id=7**：骨架相同（id=5 結構 + JSON list），差別只在 list 語意——id=7 是同帳號 sibling 密碼、id=8 是同一密碼的其他 tag-type 候選結構。
> **資料依賴**：目前 pipeline 每個 tagtype 各自獨立產 JSONL，三者未對齊；id=8 需另寫合併步驟（仿 `run_pcfg_combine_sibling.py`）把三種結構依密碼對齊打包。
