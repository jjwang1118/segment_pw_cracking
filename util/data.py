import pandas as pd
import yaml
import os
from pathlib import Path

def load_config(cpnfig_path):
    with open(cpnfig_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def load_data(data_path:str,config:dict):
    dataset=None
    for i in config['password_cleaning']['dataset']:
        
        path=Path(data_path)/f'{i}.txt'
        
        if os.path.exists(path):
            print(f"Loading dataset: {i}")

            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = [line.rstrip('\r\n') for line in f if line.strip()]
            data = pd.DataFrame(passwords, columns=['password'])
            dataset=pd.concat([dataset,data],ignore_index=True) if dataset is not None else data
        else:
            print(f"Dataset {i} not found at {path}. Skipping.")


    return dataset



def clean_data(dataset:pd.DataFrame,config:dict):
    # 長度過濾
    min_length = config['password_cleaning']['min_length']
    max_length = config['password_cleaning']['max_length']
    dataset = dataset[(dataset['password'].str.len() >= min_length) & (dataset['password'].str.len() <= max_length)]

    # 字元集過濾
    allowed_charsets = config['password_cleaning']['allowed_charsets']
    if allowed_charsets:
        charset_map = {
            'lowercase': 'a-z',
            'uppercase': 'A-Z',
            'digits':    '0-9',
            'special':   r'!-/:-@\[-`{-~',
        }
        char_class = ''.join(v for k, v in charset_map.items() if allowed_charsets.get(k))
        if char_class:
            pattern = f'^[{char_class}]+$'
            dataset = dataset[dataset['password'].str.match(pattern)]

    return dataset

def remove_duplicates(dataset:pd.DataFrame):
    return dataset.drop_duplicates().reset_index(drop=True)


def save_cleaned_data(dataset:pd.DataFrame,output_path:str):
    
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    dataset.to_csv(os.path.join(output_path, 'cleaned_data.txt'), index=False, header=False)
    


