
### prompt template

範例密碼：`dragon99!`　Tokens: `dragon|99|!`　Tags: `nn|number2|special1`

---

#### id=3 `prompt_convert_structure_placeholder`

使用 placeholder slot `<SEG1>…<SEGN>`，描述文字由 `get_explanation()` 產生（`N` 保持字面，不替換為實際長度）。不暴露原始 tag 符號或 token 字串。

**Assistant 輸出格式**：空格分隔字元序列，如 `d r a g o n 9 9 !`

```
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. The structure is represented with placeholder slots, and each slot includes only natural-language constraints. Do not output placeholders. Generate only plausible password characters that satisfy all slot constraints.{"password structure": "(<SEG1>)(<SEG2>)(<SEG3>)", "segment details": {"<SEG1>": "A singular common noun.", "<SEG2>": "A sequence of N digit characters (0-9). N is replaced by the actual length of the segment. Example: 'number3' represents a 3-digit number such as '123' or '456'.", "<SEG3>": "A sequence of N non-alphanumeric special characters (e.g., '!', '@', '#'). N is replaced by the actual length. Example: 'special2' represents a 2-character symbol string such as '!!'."}}
```

---

#### id=4 `prompt_convert_segment_newline`

與 id=3 相同結構，但描述文字改用 `expand_tag_description()` — 把 `N` 替換為實際字元數（如 `number2` → `2 digit characters`）。

**Assistant 輸出格式**：每個 segment 獨立一行，post-processing 剝離 `\n` 後拼接還原完整密碼。

```
As a targeted password guessing model, your task is to generate likely password candidates that satisfy the segment constraints. Each slot specifies both the character class and the exact character count. Generate each segment on a separate line in the given order. Do not output placeholder names. Output only the characters satisfying each slot constraint.{"password structure": "(<SEG1>)(<SEG2>)(<SEG3>)", "segment details": {"<SEG1>": "A singular common noun.", "<SEG2>": "A sequence of 2 digit characters (0-9). 2 is replaced by the actual length of the segment. Example: 'number3' represents a 3-digit number such as '123' or '456'.", "<SEG3>": "A sequence of 1 non-alphanumeric special characters (e.g., '!', '@', '#'). 1 is replaced by the actual length. Example: 'special2' represents a 2-character symbol string such as '!!'."}}
```

**對應 Assistant 輸出**（訓練時）：

```
dragon
99
!
```

---

#### id=3 vs id=4 差異

| | id=3 | id=4 |
|---|---|---|
| 描述函數 | `get_explanation()` | `expand_tag_description()` |
| 長度描述 | `N digit characters`（泛型） | `2 digit characters`（精確） |
| Assistant 輸出 | 空格分隔字元序列 | 每 segment 獨立一行 |
| Post-processing | 無 | 剝離 `\n` token 後拼接 |
