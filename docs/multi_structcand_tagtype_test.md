# Multi-StructCand 前置測試：tag-type 結構歧義

> 分支：`multi-structcand`　日期：2026-08-30
> 目的：驗證「讀法 A」的前提——同一密碼是否存在多個候選結構（1 pw → N structures），
> 本測試先檢查「三種 tag-type 併陳」是否構成有效的 N 來源。

---

## 1. 測試設定

| 項目 | 值 |
|---|---|
| 資料集 | `datasets/cleaned/rockyou-75/cleaned_data.txt` |
| 長度過濾 | 8–20（與訓練同款 `password_filter`） |
| 抽樣數 | 100 |
| 隨機種子 | 42（可重現） |
| tag-type | `pos` / `backoff` / `pos_semantic` |
| 工具 | `src/PCFGSegment.py` `PCFGSegmenter(sg_path, tagtype).segment_and_tag(pw)` |
| 腳本 | `scratchpad/tag3modes.py`（探索性，未進版控） |

三種 tag-type 共用**同一套切分**（`_getchunks` 不依賴 tagtype），差別只在 `GrammarTagger._get_tag()` 的標記層級。

---

## 2. 統計摘要

| 指標 | 結果 |
|---|---|
| 切分在三種 tagtype 間不一致 | **0 / 100** |
| 三種 tag 字串完全相同 | 10 / 100（純數字/純亂碼，如 `number8`、`char8`） |
| 有 2 種不同 tag 字串 | 14 / 100 |
| 有 3 種全不同 | 76 / 100 |
| 平均每筆「不同結構數」 | **2.66** |

---

## 3. 核心結論

### 3.1 三種 tag-type 是「抽象層級」不是「競爭假設」

三者不是同一密碼的競爭解讀，而是**同一結構的三種顆粒度**，且 segmentation 永遠相同：

- `pos` — 純 CLAWS7 詞性（最粗）：`nn1`、`np1`、`vv0`
- `pos_semantic` — `pos` + WordNet synset（最細）：`nn1_puppy.n.01`
- `backoff` — 只留語意層：`puppy.n.01`

例：`puppy` → `nn1` / `nn1_puppy.n.01` / `puppy.n.01`，本質同一決定的不同顆粒度。
因此「2.66」**高估**了真正的歧義。

### 3.2 真正有價值：三者「互補」而非「競爭」

各自丟掉對方保留的資訊，專有名詞上尤其明顯：

| 密碼 | backoff | pos | pos_semantic |
|---|---|---|---|
| `jacksparrow` | **mname\|surname** | np1\|np1 | np1_**unk**\|np1_**unk** |
| `jimenez1` | **surname**\|number1 | np1\|number1 | np1_**unk**\|number1 |
| `guimaraes` | **city** | np2 | np2_**unk** |

`backoff` 知道「男名／姓氏／城市」，但 `pos_semantic` 因專有名詞無 WordNet synset，塌成 `np1_unk`；
反過來對普通詞，`pos_semantic` 帶 POS+synset，`backoff` 沒有 POS 標籤。

**→ 三種併陳 = 嚴格多於任何單一種的資訊。**

### 3.3 對讀法 A 的意涵

1. 「3 種 tag-type」當 N，性質是**互補視角**（richer conditioning），**不等於**對不確定結構做 hedge。
2. 若要「真正競爭候選結構」（1 pw → N 個不同假設），來源需換成：
   - 多重 segmentation（`dragon99` 也可切 `drag|on|99`）
   - WordNet 多 sense：目前 `src/PCFGSegment.py:118` 寫死 `synsets[0]`，改 top-k 即天然 N 來源
   - PCFG 本身的 parse 機率分布

---

## 4. 完整原始結果（100 筆）

`#uniq` = 三種 tag 字串去重後的數量。

| # | password | tokens | backoff | pos | pos_semantic | #uniq |
|---|---|---|---|---|---|---|
| 1 | puppy123 | puppy\|123 | puppy.n.01\|number3 | nn1\|number3 | nn1_puppy.n.01\|number3 | 3 |
| 2 | memories | memories | memory.n.01 | nn2 | nn2_memory.n.01 | 3 |
| 3 | Rangers1 | Rangers\|1 | texas_ranger.n.01\|number1 | nn2\|number1 | nn2_texas_ranger.n.01\|number1 | 3 |
| 4 | looneytunes | looney\|tunes | surname\|tune.n.01 | np1\|nn2 | np1_unk\|nn2_tune.n.01 | 3 |
| 5 | holyghost | holy\|ghost | holy.a.01\|ghost.n.01 | jj\|nn1 | jj_holy.a.01\|nn1_ghost.n.01 | 3 |
| 6 | cucaracha | cucaracha | np1 | np1 | np1_unk | 2 |
| 7 | chocolate123 | chocolate\|123 | cocoa.n.01\|number3 | nn1\|number3 | nn1_cocoa.n.01\|number3 | 3 |
| 8 | jimenez1 | jimenez\|1 | surname\|number1 | np1\|number1 | np1_unk\|number1 | 3 |
| 9 | moonbeam | moonbeam | moonbeam.n.01 | nn1 | nn1_moonbeam.n.01 | 3 |
| 10 | villa123 | villa\|123 | villa.n.01\|number3 | nn1\|number3 | nn1_villa.n.01\|number3 | 3 |
| 11 | june1995 | june\|1995 | june.n.01\|number4 | npm1\|number4 | npm1_june.n.01\|number4 | 3 |
| 12 | ironmaiden | iron\|maiden | iron.n.01\|inaugural.s.01 | nn1\|jj | nn1_iron.n.01\|jj_inaugural.s.01 | 3 |
| 13 | boricua1 | boricua\|1 | np1\|number1 | np1\|number1 | np1_unk\|number1 | 2 |
| 14 | jacksparrow | jack\|sparrow | mname\|surname | np1\|np1 | np1_unk\|np1_unk | 3 |
| 15 | snowpatrol | snow\|patrol | snow.n.01\|patrol.n.01 | nn1\|nn1 | nn1_snow.n.01\|nn1_patrol.n.01 | 3 |
| 16 | family12 | family\|12 | family.n.01\|number2 | nn1\|number2 | nn1_family.n.01\|number2 | 3 |
| 17 | amymarie | amy\|marie | fname\|fname | np1\|np1 | np1_unk\|np1_unk | 3 |
| 18 | emmerson | emmerson | fname | np1 | np1_unk | 3 |
| 19 | yourmom1 | your\|mom\|1 | appge\|ma.n.01\|number1 | appge\|nn1\|number1 | appge_unk\|nn1_ma.n.01\|number1 | 3 |
| 20 | kukumalu | kuku\|malu | np1\|np1 | np1\|np1 | np1_unk\|np1_unk | 2 |
| 21 | january14 | january\|14 | january.n.01\|number2 | npm1\|number2 | npm1_january.n.01\|number2 | 3 |
| 22 | justmine | just\|mine | merely.r.01\|mine.n.01 | rr\|nn1 | rr_merely.r.01\|nn1_mine.n.01 | 3 |
| 23 | rarotonga | rarotonga | np1 | np1 | np1_unk | 2 |
| 24 | ebenezer | ebenezer | np1 | np1 | np1_unk | 2 |
| 25 | psalm139 | psalm\|139 | psalm.n.01\|number3 | nn1\|number3 | nn1_psalm.n.01\|number3 | 3 |
| 26 | 12348765 | 12348765 | number8 | number8 | number8 | 1 |
| 27 | foundation | foundation | foundation.n.01 | nn1 | nn1_foundation.n.01 | 3 |
| 28 | hernandez | hernandez | surname | np1 | np1_unk | 3 |
| 29 | bubba123 | bubba\|123 | np1\|number3 | np1\|number3 | np1_unk\|number3 | 2 |
| 30 | iloveboys! | i\|love\|boys\|! | ppis1\|love.v.01\|male_child.n.01\|special1 | ppis1\|vv0\|nn2\|special1 | ppis1_unk\|vv0_love.v.01\|nn2_male_child.n.01\|special1 | 3 |
| 31 | strikers | strikers | striker.n.01 | nn2 | nn2_striker.n.01 | 3 |
| 32 | hannamontana | hanna\|montana | fname\|fname | np1\|np1 | np1_unk\|np1_unk | 3 |
| 33 | tinkerbel1 | tinker\|bel\|1 | putter.v.02\|char3\|number1 | vvi\|char3\|number1 | vvi_putter.v.02\|char3\|number1 | 3 |
| 34 | alfaromeo | alfa\|romeo | np1\|mname | np1\|np1 | np1_unk\|np1_unk | 3 |
| 35 | heavenly1 | heavenly\|1 | celestial.a.02\|number1 | jj\|number1 | jj_celestial.a.02\|number1 | 3 |
| 36 | iloveshane | i\|love\|shane | ppis1\|love.v.01\|mname | ppis1\|vv0\|np1 | ppis1_unk\|vv0_love.v.01\|np1_unk | 3 |
| 37 | Butterfly | Butterfly | butterfly.n.01 | nn1 | nn1_butterfly.n.01 | 3 |
| 38 | davidoff | davidoff | np1 | np1 | np1_unk | 2 |
| 39 | 12345678a | 12345678\|a | number8\|char1 | number8\|char1 | number8\|char1 | 1 |
| 40 | 23102310 | 23102310 | number8 | number8 | number8 | 1 |
| 41 | ceballos | ceballos | np2 | np2 | np2_unk | 2 |
| 42 | butterfly15 | butterfly\|15 | butterfly.n.01\|number2 | nn1\|number2 | nn1_butterfly.n.01\|number2 | 3 |
| 43 | just4you | just\|4\|you | merely.r.01\|number1\|ppy | rr\|number1\|ppy | rr_merely.r.01\|number1\|ppy_unk | 3 |
| 44 | heavenly | heavenly | celestial.a.02 | jj | jj_celestial.a.02 | 3 |
| 45 | science1 | science\|1 | science.n.01\|number1 | nn1\|number1 | nn1_science.n.01\|number1 | 3 |
| 46 | anthony26 | anthony\|26 | mname\|number2 | np1\|number2 | np1_unk\|number2 | 3 |
| 47 | warfreak | war\|freak | war.n.01\|freak.n.01 | nn1\|nn1 | nn1_war.n.01\|nn1_freak.n.01 | 3 |
| 48 | ilovenikki | i\|love\|nikki | ppis1\|love.v.01\|fname | ppis1\|vv0\|np1 | ppis1_unk\|vv0_love.v.01\|np1_unk | 3 |
| 49 | poppy123 | poppy\|123 | poppy.n.01\|number3 | nn1\|number3 | nn1_poppy.n.01\|number3 | 3 |
| 50 | Password2 | Password\|2 | password.n.01\|number1 | nn1\|number1 | nn1_password.n.01\|number1 | 3 |
| 51 | baseball6 | baseball\|6 | baseball.n.01\|number1 | nn1\|number1 | nn1_baseball.n.01\|number1 | 3 |
| 52 | miguelon | miguelon | char8 | char8 | char8 | 1 |
| 53 | morientes | morientes | char9 | char9 | char9 | 1 |
| 54 | anthony21 | anthony\|21 | mname\|number2 | np1\|number2 | np1_unk\|number2 | 3 |
| 55 | underoath | underoath | np1 | np1 | np1_unk | 2 |
| 56 | JONATHAN | JONATHAN | mname | np1 | np1_unk | 3 |
| 57 | rocketman | rocketman | char9 | char9 | char9 | 1 |
| 58 | stiffler | stiffler | np1 | np1 | np1_unk | 2 |
| 59 | teamodios | team\|o\|dios | team.n.01\|char1\|char4 | nn1\|char1\|char4 | nn1_team.n.01\|char1\|char4 | 3 |
| 60 | december13 | december\|13 | december.n.01\|number2 | npm1\|number2 | npm1_december.n.01\|number2 | 3 |
| 61 | wildflower | wildflower | wildflower.n.01 | nn1 | nn1_wildflower.n.01 | 3 |
| 62 | crazybabe | crazy\|babe | brainsick.s.01\|baby.n.01 | jj\|nn1 | jj_brainsick.s.01\|nn1_baby.n.01 | 3 |
| 63 | girltalk | girl\|talk | girl.n.01\|talk.n.01 | nn1\|nn1 | nn1_girl.n.01\|nn1_talk.n.01 | 3 |
| 64 | friends08 | friends\|08 | friend.n.01\|number2 | nn2\|number2 | nn2_friend.n.01\|number2 | 3 |
| 65 | c1234567 | c\|1234567 | char1\|number7 | char1\|number7 | char1\|number7 | 1 |
| 66 | cunningham | cunningham | surname | np1 | np1_unk | 3 |
| 67 | joseph11 | joseph\|11 | mname\|number2 | np1\|number2 | np1_unk\|number2 | 3 |
| 68 | ladycute | lady\|cute | lady.n.01\|cunning.s.01 | nn1\|jj | nn1_lady.n.01\|jj_cunning.s.01 | 3 |
| 69 | hottie#1 | hottie\|#\|1 | nn1\|special1\|number1 | nn1\|special1\|number1 | nn1_unk\|special1\|number1 | 2 |
| 70 | roxanita | rox\|anita | char3\|fname | char3\|np1 | char3\|np1_unk | 3 |
| 71 | Chocolate | Chocolate | cocoa.n.01 | nn1 | nn1_cocoa.n.01 | 3 |
| 72 | teamodiego | team\|o\|diego | team.n.01\|char1\|mname | nn1\|char1\|np1 | nn1_team.n.01\|char1\|np1_unk | 3 |
| 73 | cookies7 | cookies\|7 | cookie.n.01\|number1 | nn2\|number1 | nn2_cookie.n.01\|number1 | 3 |
| 74 | luisantonio | luis\|antonio | mname\|mname | np1\|np1 | np1_unk\|np1_unk | 3 |
| 75 | sexytime | sexy\|time | sexy.a.01\|time.n.01 | jj\|nnt1 | jj_sexy.a.01\|nnt1_time.n.01 | 3 |
| 76 | julian12 | julian\|12 | mname\|number2 | np1\|number2 | np1_unk\|number2 | 3 |
| 77 | fluffy12 | fluffy\|12 | downy.s.01\|number2 | jj\|number2 | jj_downy.s.01\|number2 | 3 |
| 78 | austin10 | austin\|10 | mname\|number2 | np1\|number2 | np1_unk\|number2 | 3 |
| 79 | sammysosa | sammy\|sosa | mname\|surname | np1\|np1 | np1_unk\|np1_unk | 3 |
| 80 | lisandra | li\|sandra | char2\|fname | char2\|np1 | char2\|np1_unk | 3 |
| 81 | harvey123 | harvey\|123 | mname\|number3 | np1\|number3 | np1_unk\|number3 | 3 |
| 82 | murcielago | murcielago | nn1 | nn1 | nn1_unk | 2 |
| 83 | guimaraes | guimaraes | city | np2 | np2_unk | 3 |
| 84 | ilovemymom | i\|love\|my\|mom | ppis1\|love.v.01\|appge\|ma.n.01 | ppis1\|vv0\|appge\|nn1 | ppis1_unk\|vv0_love.v.01\|appge_unk\|nn1_ma.n.01 | 3 |
| 85 | twentyfive | twenty\|five | mc\|mc | mc\|mc | mc_unk\|mc_unk | 2 |
| 86 | penguin7 | penguin\|7 | np1\|number1 | np1\|number1 | np1_unk\|number1 | 2 |
| 87 | momsgirl | moms\|girl | ma.n.01\|girl.n.01 | nn2\|nn1 | nn2_ma.n.01\|nn1_girl.n.01 | 3 |
| 88 | 25292529 | 25292529 | number8 | number8 | number8 | 1 |
| 89 | passionate | passionate | passionate.a.01 | jj | jj_passionate.a.01 | 3 |
| 90 | breathless | breathless | breathless.a.01 | jj | jj_breathless.a.01 | 3 |
| 91 | babybitch | baby\|bitch | baby.n.01\|bitch.n.01 | nn1\|nn1 | nn1_baby.n.01\|nn1_bitch.n.01 | 3 |
| 92 | cantique | cantique | char8 | char8 | char8 | 1 |
| 93 | leahmarie | leah\|marie | fname\|fname | np1\|np1 | np1_unk\|np1_unk | 3 |
| 94 | forgiven1 | forgiven\|1 | forgive.v.01\|number1 | vvn\|number1 | vvn_forgive.v.01\|number1 | 3 |
| 95 | specialk1 | special\|k\|1 | particular.s.01\|char1\|number1 | jj\|char1\|number1 | jj_particular.s.01\|char1\|number1 | 3 |
| 96 | brandon13 | brandon\|13 | mname\|number2 | np1\|number2 | np1_unk\|number2 | 3 |
| 97 | hotcakes | hotcakes | pancake.n.01 | nn2 | nn2_pancake.n.01 | 3 |
| 98 | chicasexy | chica\|sexy | nn1\|sexy.a.01 | nn1\|jj | nn1_unk\|jj_sexy.a.01 | 3 |
| 99 | brenden1 | brenden\|1 | mname\|number1 | np1\|number1 | np1_unk\|number1 | 3 |
| 100 | khristian | k\|hristian | char1\|char8 | char1\|char8 | char1\|char8 | 1 |
