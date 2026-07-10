"""
run_pcfg_tag_presplit.py

Tag pre-split password datasets (train.txt / test.txt already split by an
external process) with PCFG tags, without resampling or reshuffling.

Cleaning applied before tagging (train/test membership is otherwise
untouched):
  1. Drop passwords containing '|' (ambiguous with the Tokens/Tags join
     delimiter, produces unparseable rows)
  2. Drop passwords containing a character outside PW_WORD (the 94-char
     vocabulary util/pw_tokenize.py:get_alpa() actually encodes/generates)
  3. Drop duplicate passwords within train.txt
  4. Drop duplicate passwords within test.txt
  5. Drop passwords from test.txt that also appear in train.txt (leakage)

Input:
  datasets/processed/{dataset}/split/train.txt
  datasets/processed/{dataset}/split/test.txt

Output (per tagtype):
  gen/semanticPCFG/{dataset}_{split}_{tagtype}_tagged.csv
  datasets/processed/semanticPCFG/{dataset}/{tagtype}/split/{train,test}_data.jsonl

Usage:
  python run_pcfg_tag_presplit.py                  # dataset=COMB, all tagtypes
  python run_pcfg_tag_presplit.py --dataset COMB --tagtype backoff
  python run_pcfg_tag_presplit.py --force
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH  = PROJECT_ROOT / "config" / "pcfg_segment.yaml"

# Not part of pcfg_segment.yaml — this script owns its own I/O layout.
PRESPLIT_RAW_DIR    = PROJECT_ROOT / "datasets" / "processed"
PROCESSED_ROOT_DIR  = PROJECT_ROOT / "datasets" / "processed" / "semanticPCFG"

# Must match PW_WORD in util/pw_tokenize.py:get_alpa() — the actual 94-char
# vocabulary the model can encode/generate. This is the real constraint, not
# config/config.yaml's password_cleaning.allowed_charsets (that policy allows
# ':' which PW_WORD excludes, and excludes ' ' which PW_WORD allows).
_PW_WORD = set(
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "!\"#$%&\'()*+,-./;<=>?@[\\]^_`{|}~ "
)


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_and_clean_split(dataset: str):
    """
    Load raw train/test password lists, drop passwords containing '|'
    (ambiguous with the Tokens/Tags join delimiter), drop internal
    duplicates, then drop test entries that leak into train.

    Returns dict: {"train": [...], "test": [...]}
    """
    split_dir  = PRESPLIT_RAW_DIR / dataset / "split"
    train_path = split_dir / "train.txt"
    test_path  = split_dir / "test.txt"

    with open(train_path, "r", encoding="utf-8", errors="ignore") as f:
        train_pw = [line.rstrip("\r\n") for line in f if line.strip()]
    with open(test_path, "r", encoding="utf-8", errors="ignore") as f:
        test_pw = [line.rstrip("\r\n") for line in f if line.strip()]

    train_before, test_before = len(train_pw), len(test_pw)
    train_pw = [pw for pw in train_pw if "|" not in pw]
    test_pw  = [pw for pw in test_pw if "|" not in pw]
    print(f"  train.txt drop '|'-containing: {train_before:,} -> {len(train_pw):,}")
    print(f"  test.txt  drop '|'-containing: {test_before:,} -> {len(test_pw):,}")

    train_before, test_before = len(train_pw), len(test_pw)
    train_pw = [pw for pw in train_pw if set(pw) <= _PW_WORD]
    test_pw  = [pw for pw in test_pw if set(pw) <= _PW_WORD]
    print(f"  train.txt drop outside-PW_WORD: {train_before:,} -> {len(train_pw):,}")
    print(f"  test.txt  drop outside-PW_WORD: {test_before:,} -> {len(test_pw):,}")

    train_before, test_before = len(train_pw), len(test_pw)
    train_pw = list(dict.fromkeys(train_pw))
    test_pw  = list(dict.fromkeys(test_pw))
    print(f"  train.txt dedup: {train_before:,} -> {len(train_pw):,}")
    print(f"  test.txt  dedup: {test_before:,} -> {len(test_pw):,}")

    train_set = set(train_pw)
    test_before_leak = len(test_pw)
    test_pw = [pw for pw in test_pw if pw not in train_set]
    print(f"  test.txt  leakage removal (present in train.txt): "
          f"{test_before_leak:,} -> {len(test_pw):,}")

    return {"train": train_pw, "test": test_pw}


def tag_split(segmenter, tagged_dir: Path, dataset: str, split_name: str,
              passwords: list, force: bool) -> pd.DataFrame:
    tagged_dir.mkdir(parents=True, exist_ok=True)
    out_path = tagged_dir / f"{dataset}_{split_name}_{segmenter.tagtype}_tagged.csv"

    if out_path.exists() and not force:
        print(f"    [skip] {out_path.name} already exists (use --force to re-run)")
        return pd.read_csv(out_path)

    print(f"    Tagging {len(passwords):,} {split_name} passwords ...")
    rows = []
    skipped = 0
    for pw in passwords:
        try:
            tokens, tags = segmenter.segment_and_tag(pw)
        except Exception:
            skipped += 1
            continue
        if not tokens:
            skipped += 1
            continue
        rows.append({"Password": pw, "Tokens": "|".join(tokens), "Tags": "|".join(tags)})

    if skipped:
        print(f"    [info] skipped {skipped:,} passwords (segmentation failed or empty)")

    df = pd.DataFrame(rows, columns=["Password", "Tokens", "Tags"])
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"    Saved {len(df):,} rows -> {out_path}")
    return df


def save_jsonl(df: pd.DataFrame, dataset: str, split_name: str, tagtype: str,
               password_filter: dict):
    min_len = password_filter["min_length"]
    max_len = password_filter["max_length"]
    before = len(df)
    df = df[
        (df["Password"].str.len() >= min_len) & (df["Password"].str.len() <= max_len)
    ].reset_index(drop=True)
    print(f"    Length filter [{min_len},{max_len}]: {before:,} -> {len(df):,}")

    df = df.copy()
    df["source"] = dataset

    out_dir = PROCESSED_ROOT_DIR / dataset / tagtype / "split"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{split_name}_data.jsonl"
    df.to_json(out_path, orient="records", lines=True, force_ascii=False)
    print(f"    Saved {len(df):,} rows -> {out_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tag pre-split (train/test already fixed) password datasets with PCFG tags"
    )
    parser.add_argument("--dataset", default="COMB", help="Presplit dataset name (default: COMB)")
    parser.add_argument(
        "--tagtype", choices=["pos", "backoff", "pos_semantic"], default=None,
        help="Run only this tagtype (default: all tagtypes in pcfg_segment.yaml)",
    )
    parser.add_argument("--force", action="store_true", help="Re-run tagging even if the CSV already exists")
    return parser.parse_args()


def main():
    args = parse_args()
    cfg  = load_config()

    tagtypes = [args.tagtype] if args.tagtype else cfg["tagtypes"]
    sg_path  = str(PROJECT_ROOT / cfg["semantic_guesser_path"])
    tagged_dir = PROJECT_ROOT / cfg["dirs"]["tagged"]

    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from PCFGSegment import PCFGSegmenter

    print(f"\n{'='*60}")
    print(f"dataset: {args.dataset}")
    print(f"{'='*60}")
    splits = load_and_clean_split(args.dataset)

    for tagtype in tagtypes:
        print(f"\n  tagtype: {tagtype}")
        segmenter = PCFGSegmenter(sg_path=sg_path, tagtype=tagtype)
        for split_name in ("train", "test"):
            df = tag_split(segmenter, tagged_dir, args.dataset, split_name,
                            splits[split_name], force=args.force)
            save_jsonl(df, args.dataset, split_name, tagtype, cfg["password_filter"])


if __name__ == "__main__":
    main()
