from tokenizers import Tokenizer
import sys
import os
import glob
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from BPE import BPE, _train_with_avg_len




# ── 主入口 ────────────────────────────────────────────────────

def trainTokenizer(config: dict) -> Tokenizer:
    cfg = config['bpe']
    tokenizer_path = os.path.join(cfg['save_path'], 'tokenizer.json')

    # 若不需重新訓練，直接載入既有 tokenizer
    if not cfg['train'] and os.path.exists(tokenizer_path):
        return Tokenizer.from_file(tokenizer_path)

    if cfg.get('avg_len') is not None:
        # PwdSegment 模式：avg_len 停止
        tokenizer, token_freq = _train_with_avg_len(cfg)
    else:
        # 標準模式：HuggingFace BpeTrainer，vocab_size 停止
        tokenizer, trainer = BPE(config)
        corpus = cfg['train_corpus']
        files = glob.glob(os.path.join(corpus, '**', '*.txt'), recursive=True) \
            if os.path.isdir(corpus) else [corpus]
        if not files:
            raise FileNotFoundError(f"找不到訓練語料：{corpus}")
        tokenizer.train(files, trainer)

    os.makedirs(cfg['save_path'], exist_ok=True)
    tokenizer.save(tokenizer_path)
    if cfg.get('avg_len') is not None:
        freq_path = os.path.join(cfg['save_path'], 'vocab_freq.json')
        with open(freq_path, 'w', encoding='utf-8') as f:
            json.dump(token_freq, f, ensure_ascii=False, indent=2)
    return tokenizer
