from tokenizers import Tokenizer
import pandas as pd
import yaml
import os


## BPE TOKENIZE動作

_DEFAULT_CFG = os.path.join(os.path.dirname(__file__), '..', 'config', 'tokenize_setting.yaml')


def _load_config(config_path: str = _DEFAULT_CFG) -> dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)['tokenize']


class Tokenizer_tag:
    def __init__(self, config_path: str = _DEFAULT_CFG):
        cfg = _load_config(config_path)
        self.cfg = cfg

        dataset = cfg['dataset']
        dirs    = cfg['dirs']

        self.tokenizer      = Tokenizer.from_file(
            os.path.join(dirs['tokenizer'], dataset, 'tokenizer.json')
        )
        self.dataset        = dataset
        self.dirs           = dirs
        self.path           = os.path.join(dirs['datasets'], f'{dataset}.txt')
        self._out_tokenized = os.path.join(dirs['tokenized'], f'{dataset}_tokenized.csv')

    def read(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            passwords = [line.strip() for line in f if line.strip() and '|' not in line]
        return passwords

    def tokenize(self, passwords):
        store = []
        for password in passwords:
            tokens = self.tokenizer.encode(password).tokens
            print(f"Password: {password} , Tokens: {tokens}\n")
            store.append((password, tokens))

        df = pd.DataFrame(
            [(pw, '|'.join(toks)) for pw, toks in store],
            columns=['Password', 'Tokens']
        )
        os.makedirs(os.path.dirname(self._out_tokenized), exist_ok=True)
        df.to_csv(self._out_tokenized, index=False, encoding='utf-8')
        print(f"Tokenization complete. Results saved to '{self._out_tokenized}'.")
        return df

    def tag(self):
        import sys

        tag_cfg = self.cfg['tagging']
        sg_path = os.path.abspath(tag_cfg['semantic_guesser_path'])
        tagtype = tag_cfg['tagtype']
        self._out_tagged = os.path.join(
            self.dirs['tagged'], f'{self.dataset}_{tagtype}_tagged.csv'
        )

        if sg_path not in sys.path:
            sys.path.insert(0, sg_path)

        from learning.pos import BackoffTagger
        from learning.model import GrammarTagger

        pos_tagger     = BackoffTagger()
        grammar_tagger = GrammarTagger()

        df = self.tokenize(self.read())
        tags_col, structure_col = [], []

        for _, row in df.iterrows():
            tokens = row['Tokens'].split('|') if isinstance(row['Tokens'], str) else row['Tokens']
            row_tags = []

            for token in tokens:
                if not token:
                    continue

                pos = pos_tagger.tag([token])[0][1]
                tag = grammar_tagger._get_tag(token, pos, None, tagtype)
                row_tags.append(tag if tag else 'unk')

            structure = ''.join(f'({t})' for t in row_tags)
            tags_col.append('|'.join(row_tags))
            structure_col.append(structure)

        df['Tags']      = tags_col
        df['Structure'] = structure_col

        os.makedirs(os.path.dirname(self._out_tagged), exist_ok=True)
        df[['Password', 'Tokens', 'Tags']].to_csv(self._out_tagged, index=False, encoding='utf-8')
        print(f"Tagging complete. Results saved to '{self._out_tagged}'.")
        return df
