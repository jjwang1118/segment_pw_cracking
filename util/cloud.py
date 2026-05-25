from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import yaml
import json
import os


def load_config(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def read_voc(path):
    with open(path, 'r', encoding='utf-8') as f:
        vocab_freq = json.load(f)
    return vocab_freq


if __name__ == "__main__":
    # 1. 載入設定
    config = load_config('config.yaml')
    cloud_cfg = config['cloud']
    vocab_freq = read_voc(cloud_cfg['data_path'])

    all_chunks = []
    for chunk, content in vocab_freq.items():
        if chunk in ('<unk>', '<pad>', '<bos>', '<eos>'):
            continue
        all_chunks.append((chunk, content['freq']))

    all_chunks.sort(key=lambda x: x[1], reverse=True)

    # 2. 取 top_k
    top_chunks = all_chunks[:cloud_cfg['top_k']]

    # 3. 生成詞雲
    freq_dict = {chunk: freq for chunk, freq in top_chunks}
    wordcloud = WordCloud(
        width=800, height=400,
        background_color='white'
    ).generate_from_frequencies(freq_dict)

    # 繪圖
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")

    # 儲存
    save_path = cloud_cfg.get('output_path', 'results/wordcloud.png')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    if not os.path.exists(save_path):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight', dpi=150)
    print(f"詞雲已儲存至 {save_path}")
    plt.show()
