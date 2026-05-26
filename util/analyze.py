#!/usr/bin/env python3
"""
BPE Tokenizer 結果分析腳本（min_frequency > 1，非 non_filter_freq/）
從專案根目錄執行：python util/analyze.py

分析項目：
  1. 各資料集 vocab_freq.json 的 Zipf's Law 驗證
  2. merged_vocab.json 低頻前 N 個 token 繪製 Word Cloud
  3. 跨資料集 token 相似度（vocab_freq.json）── 統計交集與非交集

結果輸出：gen/analysis/
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from itertools import combinations

# ── 設定 ─────────────────────────────────────────────────────
DATASETS      = ['000webhost', 'hotmail', 'phpbb']
BASE_PATH     = 'models/tokenizer'
OUTPUT_PATH   = 'gen/analysis'
BOTTOM_N      = 100          # Word Cloud 取低頻前 N 個 token
SPECIAL_TOKENS = {'<pad>', '<unk>', '<bos>', '<eos>'}


# ── 工具函式 ──────────────────────────────────────────────────
def load_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def save_json(obj, path: str):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
# 1. Zipf's Law 驗證
#    資料來源：vocab_freq.json（token → freq，含 base + BPE 合併 token）
# ═══════════════════════════════════════════════════════════════
def analyze_zipf():
    print("=" * 60)
    print("[1] Zipf's Law Validation (vocab_freq.json)")
    print("=" * 60)

    out_dir = os.path.join(OUTPUT_PATH, 'zipf')
    ensure_dir(out_dir)

    fig, axes = plt.subplots(1, len(DATASETS), figsize=(18, 5))
    stats_result = {}

    for idx, dataset in enumerate(DATASETS):
        path = os.path.join(BASE_PATH, dataset, 'vocab_freq.json')
        vocab = load_json(path)

        # 過濾特殊 token，依頻率降序排列
        freqs = sorted(
            [v for k, v in vocab.items() if k not in SPECIAL_TOKENS],
            reverse=True
        )
        ranks    = np.arange(1, len(freqs) + 1, dtype=float)
        freqs_arr = np.array(freqs, dtype=float)

        log_r = np.log10(ranks)
        log_f = np.log10(freqs_arr)

        # log-log 線性迴歸（numpy polyfit，不需 scipy）
        slope, intercept = np.polyfit(log_r, log_f, 1)
        predicted = slope * log_r + intercept
        ss_res = np.sum((log_f - predicted) ** 2)
        ss_tot = np.sum((log_f - log_f.mean()) ** 2)
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        stats_result[dataset] = {
            'n_tokens' : int(len(freqs)),
            'alpha'    : round(-slope, 4),      # Zipf 指數（正值）
            'r2'       : round(r2, 4),
            'max_freq' : int(freqs[0]),
            'min_freq' : int(freqs[-1])
        }

        ax = axes[idx]
        ax.scatter(log_r, log_f, s=5, alpha=0.4, color='steelblue', label='Observed')
        ax.plot(log_r, predicted, 'r-', linewidth=2,
                label=f'α = {-slope:.3f}\nR² = {r2:.4f}')
        ax.set_title(dataset, fontsize=13, fontweight='bold')
        ax.set_xlabel('log₁₀(Rank)', fontsize=10)
        ax.set_ylabel('log₁₀(Frequency)', fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        print(f"  {dataset:15s}  tokens={len(freqs):5d}  "
              f"α={-slope:.4f}  R²={r2:.4f}  "
              f"freq range=[{freqs[-1]}, {freqs[0]}]")

    fig.suptitle("Zipf's Law Validation — vocab_freq.json (min_freq > 1)", fontsize=14)
    plt.tight_layout()

    img_path   = os.path.join(out_dir, 'zipf_validation.png')
    stats_path = os.path.join(out_dir, 'zipf_stats.json')
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
    save_json(stats_result, stats_path)

    print(f"\n  >> 圖表：{img_path}")
    print(f"  >> 統計：{stats_path}")


# ═══════════════════════════════════════════════════════════════
# 2. Word Cloud（低頻前 N 個 token，來自 merged_vocab.json）
#    merged_vocab.json 只含 BPE 合併後的 token（不含 base 字元）
#    取頻率最低的前 BOTTOM_N 個，視覺化長尾稀有子字串
# ═══════════════════════════════════════════════════════════════
def analyze_wordcloud(bottom_n: int = BOTTOM_N):
    print("=" * 60)
    print(f"[2] Word Cloud — bottom-{bottom_n} low-freq tokens (merged_vocab.json)")
    print("=" * 60)

    out_dir = os.path.join(OUTPUT_PATH, 'wordcloud')
    ensure_dir(out_dir)

    for dataset in DATASETS:
        path  = os.path.join(BASE_PATH, dataset, 'merged_vocab.json')
        vocab = load_json(path)

        # 過濾特殊 token，依頻率升序排列取 bottom_n
        tokens = [
            (tok, info['freq'])
            for tok, info in vocab.items()
            if tok not in SPECIAL_TOKENS
        ]
        tokens.sort(key=lambda x: x[1])          # 升序 → 低頻在前
        bottom_tokens = tokens[:bottom_n]

        freq_dict = {tok: freq for tok, freq in bottom_tokens}

        # WordCloud 字型大小對應頻率，低頻 token 反而字體較小
        # 為了讓所有 token 都可見，將頻率反轉（最低頻 → 最大字）
        max_freq = max(freq_dict.values())
        inv_dict = {tok: max_freq - freq + 1 for tok, freq in freq_dict.items()}

        # freq=0 的 token 給予最小值 1，使其可出現在 Word Cloud
        inv_dict = {tok: max(1, max_freq - freq + 1) for tok, freq in freq_dict.items()}

        # 若全部 freq 相同（如全為 0），每個 token 給隨機微小差異以呈現多樣性
        if len(set(freq_dict.values())) == 1:
            import random
            random.seed(42)
            inv_dict = {tok: random.randint(1, 10) for tok in freq_dict}

        wc = WordCloud(
            width=1200, height=600,
            background_color='white',
            colormap='plasma',
            prefer_horizontal=0.6,
            min_font_size=8
        ).generate_from_frequencies(inv_dict)

        fig, ax = plt.subplots(figsize=(14, 7))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(
            f'{dataset}  -  Bottom-{bottom_n} Low-Frequency Tokens\n'
            f'(merged_vocab.json | larger font = lower frequency)',
            fontsize=13
        )
        plt.tight_layout()

        img_path  = os.path.join(out_dir, f'{dataset}_lowfreq_cloud.png')
        list_path = os.path.join(out_dir, f'{dataset}_bottom{bottom_n}_tokens.json')
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()

        # 同時儲存對應 token list（升序，含原始頻率）
        save_json({tok: freq for tok, freq in bottom_tokens}, list_path)

        min_f = bottom_tokens[0][1]  if bottom_tokens else 0
        max_f = bottom_tokens[-1][1] if bottom_tokens else 0
        print(f"  {dataset:15s}  bottom={len(bottom_tokens)}  "
              f"freq range=[{min_f}, {max_f}]  >> {img_path}")


# ═══════════════════════════════════════════════════════════════
# 3. 跨資料集 token 相似度（vocab_freq.json）
#    ── 交集（共同 token）與 非交集（各資料集獨有 token）統計
# ═══════════════════════════════════════════════════════════════
def analyze_cross_dataset():
    print("=" * 60)
    print("[3] Cross-Dataset Token Similarity (vocab_freq.json)")
    print("=" * 60)

    out_dir = os.path.join(OUTPUT_PATH, 'cross_dataset')
    ensure_dir(out_dir)

    # 載入各資料集 vocab set
    vocab_sets: dict[str, set] = {}
    for dataset in DATASETS:
        path = os.path.join(BASE_PATH, dataset, 'vocab_freq.json')
        d    = load_json(path)
        vocab_sets[dataset] = {k for k in d if k not in SPECIAL_TOKENS}

    # ── Pairwise Jaccard 相似度 ──────────────────────────────
    jaccard_result = {}
    for ds1, ds2 in combinations(DATASETS, 2):
        s1, s2 = vocab_sets[ds1], vocab_sets[ds2]
        inter  = len(s1 & s2)
        union  = len(s1 | s2)
        jaccard_result[f'{ds1} & {ds2}'] = {
            'jaccard'     : round(inter / union, 4) if union else 0,
            'intersection': inter,
            'union'       : union,
            'only_in_first' : len(s1 - s2),
            'only_in_second': len(s2 - s1)
        }

    # ── 三資料集交集（全交集）── 交集 token
    all_common: set = vocab_sets[DATASETS[0]] & vocab_sets[DATASETS[1]] & vocab_sets[DATASETS[2]]

    # ── 各資料集獨有 token（非交集：不出現在任何其他資料集）
    unique_per_ds: dict[str, set] = {
        ds: vocab_sets[ds] - set().union(*(vocab_sets[d] for d in DATASETS if d != ds))
        for ds in DATASETS
    }

    # ── 出現在恰好 2 個資料集的 token
    two_ds_only: set = set()
    for ds1, ds2 in combinations(DATASETS, 2):
        ds3 = [d for d in DATASETS if d not in (ds1, ds2)][0]
        two_ds_only |= (vocab_sets[ds1] & vocab_sets[ds2]) - vocab_sets[ds3]

    summary = {
        'vocab_sizes'      : {ds: len(vocab_sets[ds]) for ds in DATASETS},
        'pairwise_jaccard' : jaccard_result,
        'all_three_intersection': {
            'count' : len(all_common),
            'sample': sorted(all_common)[:50]
        },
        'appears_in_two_datasets': {
            'count': len(two_ds_only),
            'sample': sorted(two_ds_only)[:50]
        },
        'unique_per_dataset': {
            ds: {
                'count' : len(unique_per_ds[ds]),
                'sample': sorted(unique_per_ds[ds])[:50]
            }
            for ds in DATASETS
        }
    }
    save_json(summary, os.path.join(out_dir, 'cross_dataset_stats.json'))

    # ── 列印 ─────────────────────────────────────────────────
    print(f"  Vocab sizes: { {ds: len(vocab_sets[ds]) for ds in DATASETS} }")
    for pair, v in jaccard_result.items():
        print(f"  {pair}  Jaccard={v['jaccard']}  "
              f"∩={v['intersection']}  ∪={v['union']}")
    print(f"  全三資料集交集（交集）  : {len(all_common):4d} tokens")
    print(f"  恰好兩資料集共同        : {len(two_ds_only):4d} tokens")
    for ds in DATASETS:
        print(f"  獨有（非交集）{ds:15s}: {len(unique_per_ds[ds]):4d} tokens")

    # ── 圖1：Jaccard Heatmap ─────────────────────────────────
    n = len(DATASETS)
    grid = np.eye(n)  # 對角線為 1.0
    for i, ds1 in enumerate(DATASETS):
        for j, ds2 in enumerate(DATASETS):
            if i >= j:
                continue
            key = f'{ds1} & {ds2}'
            grid[i, j] = grid[j, i] = jaccard_result[key]['jaccard']

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(grid, cmap='YlOrRd', vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label='Jaccard Similarity')
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(DATASETS, rotation=30, ha='right')
    ax.set_yticklabels(DATASETS)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f'{grid[i,j]:.3f}',
                    ha='center', va='center', fontsize=12,
                    color='black' if grid[i,j] < 0.6 else 'white')
    ax.set_title('Pairwise Jaccard Similarity\n(vocab_freq.json)', fontsize=12)
    plt.tight_layout()
    heatmap_path = os.path.join(out_dir, 'jaccard_heatmap.png')
    plt.savefig(heatmap_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n  >> Heatmap：{heatmap_path}")

    # ── 圖2：Intersection vs Non-intersection bar chart ──────
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 左圖：intersection / 2-dataset overlap / unique
    categories = ['All-3 Intersection', '2-Dataset Overlap', 'Unique (sum)']
    counts = [
        len(all_common),
        len(two_ds_only),
        sum(len(unique_per_ds[ds]) for ds in DATASETS)
    ]
    colors = ['#2196F3', '#FF9800', '#F44336']
    bars = axes[0].bar(categories, counts, color=colors)
    for bar, cnt in zip(bars, counts):
        axes[0].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + max(counts) * 0.01,
                     str(cnt), ha='center', va='bottom', fontsize=11)
    axes[0].set_title('Intersection vs Non-intersection Tokens', fontsize=12)
    axes[0].set_ylabel('Token Count')
    axes[0].grid(axis='y', alpha=0.3)

    # 右圖：unique (non-intersection) tokens per dataset
    unique_counts = [len(unique_per_ds[ds]) for ds in DATASETS]
    ds_colors = ['#4C72B0', '#DD8452', '#55A868']
    bars2 = axes[1].bar(DATASETS, unique_counts, color=ds_colors)
    for bar, cnt in zip(bars2, unique_counts):
        axes[1].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + max(unique_counts) * 0.01,
                     str(cnt), ha='center', va='bottom', fontsize=11)
    axes[1].set_title('Unique (Non-intersection) Tokens per Dataset', fontsize=12)
    axes[1].set_ylabel('Token Count')
    axes[1].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    bar_path = os.path.join(out_dir, 'overlap_analysis.png')
    plt.savefig(bar_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  >> 統計圖：{bar_path}")
    print(f"  >> JSON：{os.path.join(out_dir, 'cross_dataset_stats.json')}")


# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))   # 切換至專案根目錄
    ensure_dir(OUTPUT_PATH)

    analyze_zipf()
    print()
    analyze_wordcloud()
    print()
    analyze_cross_dataset()

    print("\n" + "=" * 60)
    print(f"完成！所有結果已輸出至 {OUTPUT_PATH}/")
    print("=" * 60)
