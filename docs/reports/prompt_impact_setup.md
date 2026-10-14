# Prompt 影響實驗 — 控制變因設定（COMB / COMB_MIX 兩組）

> 本文件整理「用來說明 prompt 影響」的實驗分組與**固定內容**。核心原則：每組內部只讓 **prompt** 變動，其餘全部固定；兩組之間因資料集不同，不可直接比較絕對數字。

---

## 一、所有 run 共用的固定設定（兩組完全相同）

以下項目在 **run_9 / 19 / 20 / 21 / 22 / 23** 全部一致，逐一讀自各 `train_config_snapshot.json` 確認：

| 類別 | 參數 | 固定值 |
|---|---|---|
| **訓練排程** | num_train_epochs | 10 |
| | per_device_train_batch_size | 4 |
| | gradient_accumulation_steps | 64 |
| | 有效 batch size | 256 |
| | warmup_ratio | 0.1 |
| | learning_rate | 2e-4 |
| | weight_decay | 0.01 |
| | label_smoothing_factor | 0 |
| | optimizer | adamw_torch |
| | bf16 | true |
| | seed / data_seed | 42 / 42 |
| **LoRA** | lora_kind | lora（標準 bf16 LoRA，非 QLoRA） |
| | r | 16 |
| | lora_alpha | 32 |
| | lora_dropout | 0.2 |
| | target_modules | q_proj, k_proj, v_proj |
| | bias | none |
| | init_lora_weights | true |
| **Tag 類型** | kind | backoff（主結構） |
| **評估** | 測試集大小 | 5,000 筆 |
| | 搜尋法 | constrained_beam_search（run_20 另用 dynamic 取最高） |
| | max guess number | 1,000 |
| | 評估指標 | crack rate @1 / @10 / @50 / @100 / @500 / @1000 |

> 補充：learning_rate 固定為 2e-4，`lr=5e-4` 的舊 run（run_16/17）不在本比較內；r32/α64 的 run（run_16/17/18）亦不在本比較內——本設定一律使用 r16/α32/qkv。

---

## 二、兩組的差異（唯一跨組變因 = 資料集）

| 項目 | 第一組：**COMB** | 第二組：**COMB_MIX** |
|---|---|---|
| 密碼集（md5 of sorted passwords） | `e1d6d01e…` | `5ff33669…` |
| 訓練筆數 | 262,263 | 378,719 |
| 密碼範例 | `31december` | `25031984v` |
| 目錄別名 | `combine/`、`COMB/multistruct` | `COMB_MIX/`、`combine_acc_sibling/` |
| 測試集 | COMB 5,000 | COMB_MIX 5,000 |

> 兩組密碼集 md5 不同、筆數不同、測試集不同，**絕對 crack rate 不可跨組比較**；只能做「趨勢一致性」的定性觀察。

---

## 三、第一組（COMB）— 變動的只有 prompt 線索

密碼集相同（md5 `e1d6d01e…`），只差提示欄位與 prompt template。

| run | 模型 | prompt id | 線索內容 | 額外欄位 | 備註 |
|---|---|---|---|---|---|
| run_19 | Mistral-7B | 7 | 姊妹密碼 | `Siblings` | 訓練完成（跑滿 10,250 步） |
| run_20 | Mistral-7B | 8 | 多結構候選 | `CandTags` | **訓練未跑完**（best point step 4,100） |
| run_9 | **Qwen3-4B** | 7 | 姊妹密碼（同 run_19） | `Siblings` | 中途 checkpoint（step 6,140）；**模型不同** |

**乾淨對照：**
- **run_19 vs run_20**（同為 Mistral）：姊妹密碼 vs 多結構候選 → 純 prompt 對照。
- **run_19 vs run_9**：相同 prompt(id=7)、相同資料，**唯一差別是模型**（Mistral vs Qwen）→ 這是模型對照，不是 prompt 對照。

---

## 四、第二組（COMB_MIX）— 變動的只有 prompt

密碼集相同（md5 `5ff33669…`），全為 Mistral-7B，只差 prompt template 與組裝格式。

| run | 模型 | prompt id | 差異 | 額外欄位 | 備註 |
|---|---|---|---|---|---|
| run_21 | Mistral-7B | 5 | tag-only（無線索） | 無 | tag-only 基準 |
| run_22 | Mistral-7B | 7 | +姊妹密碼（JSON list） | `Siblings` | — |
| run_23 | Mistral-7B | 9 | +姊妹密碼（sequence 串接） | `Siblings` | 實測 prompt **未含 account**，等同 run_22 的格式變體 |

**乾淨對照：**
- **run_21 vs run_22**：有無姊妹密碼 → prompt 內容對照。
- **run_22 vs run_23**：JSON vs sequence → prompt 組裝格式對照（內容相同）。

---

## 五、使用原則

1. **分兩組比**：COMB 一組、COMB_MIX 一組，各自內部比較。
2. **不可跨組比絕對值**：兩組訓練密碼與測試集都不同。
3. **注意三個非 prompt 變因**（報告中需標注）：
   - run_9 是 **Qwen**（其餘皆 Mistral）；
   - run_20 **訓練未完成**；
   - run_23 **未實際納入 account**（雖為 id=9）。
