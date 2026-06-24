# 為什麼 PCFG-native 切分比 BPE 更適合本系統

## 核心問題：切分目的不同

BPE（Byte-Pair Encoding）的設計目標是**壓縮語料**：在給定詞彙量上限的前提下，以最少的 token 數表示最多的文字。它的合併規則完全由語料頻率驅動，與密碼的語意結構無關。

PCFG-native 切分的目標是**還原密碼的字元類型邊界**：將連續的字母段、數字段、符號段分開，並在字母段內進一步以詞邊界（`wordsegment`）切分出有意義的英文單字。這與 PCFG 的語法規則天然一致。

---

## 具體差異：以 `dragon99!` 為例

| 切分方式 | 切分結果 | Tag 結果 |
|----------|----------|----------|
| BPE (avg_len=4.5) | `drag \| on \| 99 \| !` | `char4 \| char2 \| number2 \| special1` |
| PCFG-native | `dragon \| 99 \| !` | `nn \| number2 \| special1` |

BPE 把 `dragon` 拆成 `drag` + `on`，因為這兩個子字串在語料中出現頻率高。但對密碼猜測而言，`dragon` 是一個有語意的英文單字（名詞 `nn`），強行切斷後：
- LLM 看到的是 `char4` + `char2`，而非 `nn`
- 模型無法學到「`nn` tag 對應整個英文單字」的規律
- 生成時難以從 `nn` 恢復出 `dragon` 這樣的完整詞彙

---

## 訓練 Prompt 的影響

本系統的訓練 prompt（`prompt_template_id=1`）格式如下：

```json
{
  "This password can be segmented and tag into the following part": [
    ["dragon", "nn"],
    ["99", "number2"],
    ["!", "special1"]
  ],
  "For each segment, each tag represents the following meaning": {
    "nn": "common noun (singular)",
    "number2": "2-digit numeric string",
    "special1": "1-character special symbol"
  }
}
```

若改用 BPE 切分，同一個密碼的 prompt 變成：

```json
{
  "This password can be segmented and tag into the following part": [
    ["drag", "char4"],
    ["on", "char2"],
    ["99", "number2"],
    ["!", "special1"]
  ],
  ...
}
```

BPE 版本的 prompt 傳遞給 LLM 的是「`char4` + `char2` 組成某個字串」這種低語意資訊，LLM 難以從中學到有意義的詞彙生成規律。PCFG-native 版本則傳遞了「這個密碼包含一個名詞、一個兩位數字、一個符號」的高語意資訊，更貼近人類設定密碼的認知模式。

---

## 為什麼這對 Targeted 攻擊特別重要

Targeted 攻擊的前提是攻擊者掌握關於目標的部分資訊。PCFG-native 的切分方式讓 tag 具備語意可解釋性：

- `fname` tag → 攻擊者知道目標姓名（Alice）
- `nn` tag → 密碼中包含一個普通名詞
- `number2` tag → 密碼末尾有兩位數字

這些資訊在 BPE 切分下全部退化為 `char5`、`char2`、`number2`，語意完全喪失。

---

## Tag 類型的選擇順序

| Tag | 優點 | 缺點 | 建議 |
|-----|------|------|------|
| `backoff` | 100% 覆蓋率，零噪音 | 無語意（`char4` 無法區分 `dragon` vs `apple`） | 第一個訓練，作為 baseline |
| `pos` | 區分名詞/動詞/形容詞 | 非英文詞退化為 `char4` | 在 backoff baseline 後測試 |
| `pos_semantic` | 最豐富（`fname`、`city`、WordNet synset） | Tag 碎片化嚴重，稀有 tag 樣本少 | 待 pos 確認有效後再考慮 |

`backoff` 雖然語意最淺，但它的一致性讓 LLM 能穩定學習「字元類型結構 → 字元序列」的映射，是信噪比最高的起點。

---

## 實驗設計建議

為了定量驗證上述分析，建議以下控制實驗：

```
run_2: BPE + backoff          (已完成，作為 legacy baseline)
run_3: PCFG-native + backoff  (控制變數：只換切分方式)
run_4: PCFG-native + pos      (控制變數：只換 tag 類型)
```

比較 run_2 vs run_3 的 Crack rate @ K（K = 1, 10, 100, 1000），可以直接量化 PCFG-native 切分帶來的提升。
若 run_3 明顯優於 run_2，則確認切分語意對齊的重要性。
若 run_4 進一步優於 run_3，則確認 POS 語意 tag 的額外貢獻。
