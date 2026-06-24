# Tag Description 修改紀錄

**日期**：2026-06-13  
**修改檔案**：`pcfg_tags.py` → `dictionary`

---

## 問題背景

在 `run_4`（template id=2，structure-only）的 eval 結果中，模型輸出的猜測密碼幾乎全部包含 tag 描述裡的文字，而非真實的密碼內容。例如：

| 真實密碼 | Tags | 模型 top-1 猜測 | 污染來源 |
|---------|------|----------------|---------|
| `karamell` | `fname\|np1` | `EmilyCLAWS7` | fname 描述含 `'Emily'`；np1 描述含 `CLAWS7` |
| `alfa151280331` | `np1\|number9` | `np1number9` | 模型直接輸出 tag 名稱字串 |
| `89518558054koso` | `number11\|np1` | `(number11)CLAWS7` | 描述格式 `(number11)` + `CLAWS7` |

根本原因：template id=2 不提供真實 token，模型唯一的文字錨點是 descriptions。當描述包含具體的 surface form（`Emily`、`CLAWS7`、`paris`），模型學到的映射是「看到這個 tag context → 輸出描述裡的例字」，而非學習真實密碼分布。

---

## 修改原則

| 規則 | 說明 |
|------|------|
| **移除 `CLAWS7`** | 所有 POS tag 描述開頭的 `"CLAWS7 part-of-speech tag for"` 全部替換為自然語言描述。`CLAWS7` 是系統名稱，不應出現在描述文字中 |
| **移除 named entity 具體例字** | `fname`、`mname`、`city`、`surname`、`country`、`np`、`np1`、`np2` 的括號例字全部刪除，只保留類別語義 |
| **移除 open-class 詞的具體例字** | `nn`、`vv0`～`vvz`、`jj`、`jjr`、`jjt`、`rr` 等開放類別詞的例字（`'food'`、`'love'`、`'give'` 等）刪除 |
| **保留 function word 例字** | 閉集合功能詞（代名詞、冠詞、be/do/have 動詞、情態動詞）的例字保留，因為例字本身就是正確輸出值 |
| **保留 structural tag 格式說明** | `numberN`、`specialN`、`charN`、`mixedN` 的格式範例（`'123'`、`'!!'`）保留，這些不會造成 content bias |

---

## 逐條修改對照

### Named Entity Tags

| Tag | 修改前 | 修改後 |
|-----|--------|--------|
| `fname` | `"A token recognized as a female given name based on a curated name list (e.g., 'Emily', 'Jessica'). Used as a proper noun semantic tag."` | `"A female given name."` |
| `mname` | `"A token recognized as a male given name based on a curated name list (e.g., 'Jacob', 'Michael'). Used as a proper noun semantic tag."` | `"A male given name."` |
| `city` | `"A token recognized as a city name based on a curated geographic list (e.g., 'paris', 'london'). Used as a proper noun semantic tag."` | `"A city name."` |
| `surname` | `"A token recognized as a family name or last name based on a curated surname list (e.g., 'smith', 'johnson'). Used as a proper noun semantic tag."` | `"A family name or last name."` |
| `country` | `"A token recognized as a country name based on a curated geographic list (e.g., 'france', 'china'). Used as a proper noun semantic tag."` | `"A country name."` |

### Proper Noun POS Tags

| Tag | 修改前 | 修改後 |
|-----|--------|--------|
| `np` | `"CLAWS7 part-of-speech tag for a proper noun, typically a named entity (e.g., 'Jacob', 'London')."` | `"A proper noun — a person, place, or named entity."` |
| `np1` | `"CLAWS7 part-of-speech tag for a singular proper noun (e.g., 'Paris', 'John'). Assigned by the COCA or corpus-trained tagger."` | `"A singular proper noun — a person's name, place, or named entity."` |
| `np2` | `"CLAWS7 part-of-speech tag for a plural proper noun (e.g., 'Americans', 'Romans')."` | `"A plural proper noun."` |

### Common Noun POS Tags

| Tag | 修改前 | 修改後 |
|-----|--------|--------|
| `nn` | `"CLAWS7 part-of-speech tag for a singular common noun (e.g., 'food', 'love', 'house'). Derived from WordNet noun synsets."` | `"A singular common noun."` |
| `nn1` | `"CLAWS7 part-of-speech tag for a singular common noun, equivalent to 'nn'. Assigned by corpus-trained taggers (e.g., 'book', 'dog')."` | `"A singular common noun."` |
| `nn2` | `"CLAWS7 part-of-speech tag for a plural common noun (e.g., 'houses', 'books', 'dogs')."` | `"A plural common noun."` |

### Verb POS Tags

| Tag | 修改前 | 修改後 |
|-----|--------|--------|
| `vv0` | `"CLAWS7 part-of-speech tag for the base form of a main verb (infinitive). Example: 'give', 'run', 'love'."` | `"A main verb in base/infinitive form."` |
| `vvd` | `"CLAWS7 part-of-speech tag for the past tense form of a main verb. Example: 'gave', 'loved', 'ran'."` | `"A main verb in past tense form."` |
| `vvg` | `"CLAWS7 part-of-speech tag for the present participle (-ing form) of a main verb. Example: 'giving', 'loving', 'running'."` | `"A main verb in present participle (-ing) form."` |
| `vvn` | `"CLAWS7 part-of-speech tag for the past participle form of a main verb. Example: 'given', 'loved', 'run'."` | `"A main verb in past participle form."` |
| `vvz` | `"CLAWS7 part-of-speech tag for the third-person singular present tense of a main verb. Example: 'gives', 'loves', 'runs'."` | `"A main verb in third-person singular present tense."` |
| `vvi` | `"CLAWS7 part-of-speech tag for a main verb in the infinitive form (after 'to')."` | `"A main verb in infinitive form (after 'to')."` |
| `vvgk` | `"CLAWS7 part-of-speech tag for the -ing form of a main verb in a reduced clause (e.g., 'knowing', 'doing')."` | `"A main verb in -ing form used in a reduced clause."` |

### Adjective / Adverb POS Tags

| Tag | 修改前 | 修改後 |
|-----|--------|--------|
| `jj` | `"CLAWS7 part-of-speech tag for a general adjective. Example: 'great', 'hot', 'beautiful'."` | `"A general adjective."` |
| `jjr` | `"CLAWS7 part-of-speech tag for a comparative adjective. Example: 'greater', 'hotter', 'more beautiful'."` | `"A comparative adjective."` |
| `jjt` | `"CLAWS7 part-of-speech tag for a superlative adjective. Example: 'greatest', 'hottest'."` | `"A superlative adjective."` |
| `rr` | `"CLAWS7 part-of-speech tag for a general adverb. Example: 'quickly', 'always', 'never'."` | `"A general adverb."` |
| `rrr` | `"CLAWS7 part-of-speech tag for a comparative adverb. Example: 'faster', 'more quickly'."` | `"A comparative adverb."` |

### Special Noun Tags

| Tag | 修改前 | 修改後 |
|-----|--------|--------|
| `npm1` | `"CLAWS7 part-of-speech tag for a singular month name (e.g., 'January', 'March')."` | `"A month name."` |
| `npm2` | `"CLAWS7 part-of-speech tag for a plural month name (e.g., 'Januaries')."` | `"A plural month name."` |
| `npd1` | `"CLAWS7 part-of-speech tag for a singular day-of-week proper noun (e.g., 'Monday', 'Friday')."` | `"A day-of-week name."` |
| `npd2` | `"CLAWS7 part-of-speech tag for a plural day-of-week proper noun (e.g., 'Mondays')."` | `"A plural day-of-week name."` |

### Combined Semantic Tags

| Tag | 修改前 | 修改後 |
|-----|--------|--------|
| `<pos>_<synset>` | `"A combined tag used in 'pos_semantic' tagtype, concatenating the **CLAWS7** part-of-speech tag and the WordNet synset..."` | `"A combined tag encoding both syntactic role and semantic meaning."` |
| `<pos>_unk` | `"A combined tag used in 'pos_semantic' tagtype when a token has a valid part-of-speech but no matching WordNet synset. The suffix '_unk' indicates semantic unknownness."` | `"A combined tag where the token has a valid part-of-speech but no matching semantic entry."` |

### 其餘 ~60 個 POS Tags（批次規則）

所有格式為 `"CLAWS7 part-of-speech tag for X"` 的描述均改為 `"X"`（首字大寫），包含：

- 所有代名詞（`ppis1`、`ppy`、`pphs1`、`ppio1`、`pn`、`ppge` 等）
- 所有冠詞（`at`、`at1`）
- 所有介詞／連接詞（`ii`、`io`、`cc`、`cs`、`to`、`csa` 等）
- 所有 be/do/have 動詞形式（`vb0`～`vbn`、`vd0`～`vdn`、`vh0`～`vhn`）
- 限定詞（`da`、`db`、`dd`、`ddq` 等）
- 其他雜項（`uh`、`ex`、`fw`、`ge`、`xx`、`zz1`、`zz2` 等）

---

## 不需修改的項目

| Tag | 原因 |
|-----|------|
| `numberN` / `specialN` / `charN` / `mixedN` | 格式範例不造成 content bias；`'123'`、`'!!'` 不會被 copy 成密碼 |
| `at` (`'the'`)、`ppis1` (`'I'`) 等閉集合功能詞 | 例字即為正確輸出；不影響生成偏向 |
| `vm` (`'can', 'will', 'may'`) | 情態動詞為閉集合，例字幫助模型選詞 |
| `<lemma>.<pos>.<id>` | WordNet synset 格式說明，使用的例字是 synset ID 而非可輸出的 surface form |
