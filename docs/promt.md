
### prompt template

範例密碼：`dragon99!`　Tokens: `dragon|99|!`　Tags: `nn|number2|special1`

---

#### id=3 `prompt_convert_structure_placeholder`

使用 placeholder slot `<SEG1>…<SEGN>`，描述文字由 `get_explanation()` 產生（`N` 已替換為實際長度，如 `number2` → `"A sequence of exactly 2 digit characters (0-9)."`）。不暴露原始 tag 符號或 token 字串。

**Assistant 輸出格式**：空格分隔字元序列，如 `d r a g o n 9 9 !`

```
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. The structure is represented with placeholder slots, and each slot includes only natural-language constraints. Do not output placeholders. Generate only plausible password characters that satisfy all slot constraints.{"password structure": "(<SEG1>)(<SEG2>)(<SEG3>)", "segment details": {"<SEG1>": "A singular common noun.", "<SEG2>": "A sequence of exactly 2 digit characters (0-9).", "<SEG3>": "Exactly 1 non-alphanumeric special character (e.g., '!', '@', '#')."}}
```

---

#### id=4 `prompt_convert_segment_newline`

與 id=3 相同結構，但描述文字改用 `expand_tag_description()` — 格式為 `tag — short description`（如 `number2 — 2-digit number`）。

**Assistant 輸出格式**：每個 segment 獨立一行，post-processing 剝離 `\n` 後拼接還原完整密碼。

```
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. Each slot specifies both the character class and the exact character count. Generate each segment on a separate line in the given order. Do not output placeholder names. Output only the characters satisfying each slot constraint.{"password structure": "(<SEG1>)(<SEG2>)(<SEG3>)", "segment details": {"<SEG1>": "nn — singular common noun", "<SEG2>": "number2 — 2-digit number", "<SEG3>": "special1 — 1 special character"}}
```

**對應 Assistant 輸出**（訓練時）：

```
dragon
99
!
```

---

#### id=5 `prompt_convert_inline`

將 tag 名稱直接作為佔位符，緊接著對應的 segment 文字，不加任何說明。格式為 `<tag>segment` 連續串接在單一 `password structure` 字串中。

**訓練時**（有 Tokens）：

```
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. The structure is represented with placeholder slots, and each slot includes only natural-language constraints. Do not output placeholders. Generate only plausible password characters that satisfy all slot constraints.{"password structure": "<nn>dragon<number2>99<special1>!"}
```

**推理時**（只有 Tags，segment 遮住）：

```
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. The structure is represented with placeholder slots, and each slot includes only natural-language constraints. Do not output placeholders. Generate only plausible password characters that satisfy all slot constraints.{"password structure": "<nn><number2><special1>"}
```

---

#### id=3 / id=4 / id=5 差異

| | id=3 | id=4 | id=5 |
|---|---|---|---|
| 描述函數 | `get_explanation()`（N 已展開） | `expand_tag_description()` | 無描述 |
| Tag 呈現 | `<SEG1>` + 自然語言說明 | `<SEG1>` + `tag — short` | `<tag>` 直接作佔位符 |
| Segment 內容 | 不包含 | 不包含 | 訓練含、推理遮 |
| Assistant 輸出 | 空格分隔字元序列 | 每 segment 獨立一行 | 空格分隔字元序列 |
| Post-processing | 無 | 剝離 `\n` token 後拼接 | 無 |
