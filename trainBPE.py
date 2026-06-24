import os
import json
from collections import Counter
import util.data  as data_util
from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders, processors
from src.BPE import BPE
from util.trainTokenizer import _train_with_avg_len


if __name__ == "__main__":
    # 1. 載入設定
    config = data_util.load_config('config/config.yaml')

    # 2. 載入並清洗密碼資料
    dataset = data_util.load_data(config['password_cleaning']['data_path'], config)
    cleaned_dataset = data_util.clean_data(dataset, config)
    unique_dataset = data_util.remove_duplicates(cleaned_dataset)

    # 3. 訓練 BPE Tokenizer
    cfg = config['bpe']
    save_path = cfg['save_path']
    os.makedirs(save_path, exist_ok=True)

    tokenizer_path = os.path.join(save_path, 'tokenizer.json')
    already_trained = not cfg.get('train', True) and os.path.exists(tokenizer_path)

    if already_trained:
        print(f"載入既有 tokenizer：{tokenizer_path}")
        tokenizer = Tokenizer.from_file(tokenizer_path)
        with open(os.path.join(save_path, 'vocab_freq.json'), 'r', encoding='utf-8') as f:
            token_freq = json.load(f)
    elif cfg.get('avg_len') is not None:
        # PwdSegment 模式
        tokenizer, token_freq = _train_with_avg_len(cfg)
    else:
        # 標準模式：HuggingFace BpeTrainer
        tokenizer, trainer = BPE(config)
        tokenizer.train_from_iterator(unique_dataset['password'], trainer=trainer)
        # 訓練後 encode 所有密碼，統計 token 頻率
        counter: Counter = Counter()
        for pwd in unique_dataset['password']:
            counter.update(tokenizer.encode(pwd).tokens)
        token_freq = dict(counter.most_common())

    # 4. 儲存訓練好的 tokenizer 與詞彙頻率（train=false 時跳過，直接使用既有檔案）
    if not already_trained:
        tokenizer.save(os.path.join(save_path, 'tokenizer.json'))
        with open(os.path.join(save_path, 'vocab_freq.json'), 'w', encoding='utf-8') as f:
            json.dump(token_freq, f, ensure_ascii=False, indent=2)

    # 5. 合併 vocab（token→id）與頻率，依頻率排序儲存
    special_tokens = set(cfg.get('special_tokens', []))
    vocab = tokenizer.get_vocab()  # {token: id}

    # vocab_with_freq：所有 token（含單字元），供完整參考
    vocab_with_freq = {
        token: {"id": vocab[token], "freq": token_freq.get(token, 0)}
        for token in sorted(vocab, key=lambda t: -token_freq.get(t, 0))
    }
    with open(os.path.join(save_path, 'vocab_with_freq.json'), 'w', encoding='utf-8') as f:
        json.dump(vocab_with_freq, f, ensure_ascii=False, indent=2)

    # merged_vocab：只保留合併後的多字元 token（排除單字元與特殊 token）
    merged_vocab = {
        token: {"id": vocab[token], "freq": token_freq.get(token, 0)}
        for token in sorted(vocab, key=lambda t: -token_freq.get(t, 0))
        if len(token) >= 2 and token not in special_tokens
    }
    with open(os.path.join(save_path, 'merged_vocab.json'), 'w', encoding='utf-8') as f:
        json.dump(merged_vocab, f, ensure_ascii=False, indent=2)

    print(f"Tokenizer 已儲存至 {save_path}/tokenizer.json")
    print(f"詞彙頻率已儲存至 {save_path}/vocab_freq.json")
    print(f"完整詞彙表已儲存至 {save_path}/vocab_with_freq.json")
    print(f"合併詞彙表已儲存至 {save_path}/merged_vocab.json")