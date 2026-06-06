import pandas as pd
from util.data import load_config, load_data, clean_data, remove_duplicates, save_cleaned_data


if __name__ == "__main__":
    # 1. 載入設定
    config = load_config('config/config.yaml')

    # 2. 清洗密碼資料
    dataset = load_data(config['password_cleaning']['data_path'], config)
    cleaned_dataset = clean_data(dataset, config)
    unique_dataset = remove_duplicates(cleaned_dataset)
    save_cleaned_data(unique_dataset, config['password_cleaning']['output_path'])

