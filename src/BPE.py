from tokenizers import Tokenizer, trainers, models
from collections import defaultdict
import os
import glob


def BPE(config: dict) -> tuple:
    cfg = config['bpe']

    # 建立 BPE 模型（unk_token 對應 special_tokens 中的 <unk>）
    tokenizer = Tokenizer(models.BPE(unk_token='<unk>'))

    # 定義 Trainer  
    # 密碼為字元序列，不設 end_of_word_suffix（避免混淆密碼結構）
    trainer = trainers.BpeTrainer(
        vocab_size=cfg['vocab_size'],
        min_frequency=cfg['min_frequency'],
        special_tokens=cfg['special_tokens'],
        show_progress=cfg['show_progress'],
    )

    return tokenizer, trainer


# ── 共用工具 ──────────────────────────────────────────────────

def _load_passwords(cfg: dict) -> dict:
    """從語料路徑讀取密碼，回傳 {password: frequency}"""
    corpus = cfg['train_corpus']
    files = glob.glob(os.path.join(corpus, '**', '*.txt'), recursive=True) \
        if os.path.isdir(corpus) else [corpus]
    if not files:
        raise FileNotFoundError(f"找不到訓練語料：{corpus}")

    pwd_freq: dict = {}
    for f in files:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
            for line in fh:
                pwd = line.rstrip('\n')
                if pwd:
                    pwd_freq[pwd] = pwd_freq.get(pwd, 0) + 1
    return pwd_freq


# ── PwdSegment 模式：avg_len 停止的自訂 BPE 迴圈 ─────────────

def _train_with_avg_len(cfg: dict) -> Tokenizer:
    avg_len_threshold: float = cfg['avg_len']
    min_freq: int = cfg.get('min_frequency', 2)
    special_tokens: list = cfg.get('special_tokens', [])
    show_progress: bool = cfg.get('show_progress', False)

    # Step 1: 讀取語料
    pwd_freq = _load_passwords(cfg)

    # Step 2: 初始化 — 每個密碼拆成字元 tuple，記錄頻率
    word_freqs: dict = {tuple(pwd): freq for pwd, freq in pwd_freq.items()}
    vocab: set = set()
    for word in word_freqs:
        vocab.update(word)

    # Step 3: 迭代合併
    merges: list = []
    while True:
        # 統計相鄰 pair 頻率（依密碼出現頻率加權）
        pair_freqs: dict = defaultdict(int)
        for word, freq in word_freqs.items():
            for i in range(len(word) - 1):
                pair_freqs[(word[i], word[i + 1])] += freq

        # 過濾低頻 pair
        valid = {p: f for p, f in pair_freqs.items() if f >= min_freq}
        if not valid:
            break

        # 最高頻；同頻時取字典序最小（與論文一致）
        best = min(valid, key=lambda p: (-valid[p], p[0], p[1]))
        merged = best[0] + best[1]
        vocab.add(merged)
        merges.append(best)

        # 更新 word_freqs：將 best pair 替換成 merged token
        new_word_freqs: dict = {}
        for word, freq in word_freqs.items():
            new_word = []
            i = 0
            while i < len(word):
                if i < len(word) - 1 and word[i] == best[0] and word[i + 1] == best[1]:
                    new_word.append(merged)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            key = tuple(new_word)
            new_word_freqs[key] = new_word_freqs.get(key, 0) + freq
        word_freqs = new_word_freqs

        # 停止條件 1：avg_len 達到閾值
        non_special = [t for t in vocab if t not in special_tokens]
        current_avg = sum(len(t) for t in non_special) / len(non_special) if non_special else 0.0
        if show_progress:
            print(f"  vocab={len(vocab):5d}  avg_len={current_avg:.3f}  merged='{merged}'")
        if current_avg >= avg_len_threshold:
            break

        # 停止條件 2：vocab_size 上限
        if len(vocab) + len(special_tokens) >= cfg.get('vocab_size', float('inf')):
            break

    # Step 4: 計算最終詞彙表頻率（從 word_freqs 累加）
    token_freq: dict = defaultdict(int)
    for word, freq in word_freqs.items():
        for token in word:
            token_freq[token] += freq
    # 依頻率由高到低排序
    token_freq = dict(sorted(token_freq.items(), key=lambda x: -x[1]))

    # Step 5: 組建 HuggingFace Tokenizer（從學到的 vocab + merges 建立）
    token_to_id: dict = {}
    for st in special_tokens:
        token_to_id[st] = len(token_to_id)
    for token in sorted(vocab):
        if token not in token_to_id:
            token_to_id[token] = len(token_to_id)

    tokenizer = Tokenizer(models.BPE(
        vocab=token_to_id,
        merges=[(a, b) for a, b in merges],
        unk_token='<unk>' if '<unk>' in special_tokens else None,
    ))
    return tokenizer, token_freq



