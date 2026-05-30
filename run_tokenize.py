from src.Tokenize import Tokenizer_tag


def main():
    tokenizer = Tokenizer_tag()
    df = tokenizer.tag()
    print(df[['Password', 'Tokens', 'Tags', 'Structure']].head(10).to_string())


if __name__ == '__main__':
    main()
