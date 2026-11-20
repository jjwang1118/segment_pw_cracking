"""
run_pagpass_combine_acc_sibling.py

PagPassGPT counterpart of run_pcfg_combine_acc_sibling.py.

Same flow — combine PassLLM PII (sibling passwords + account name) with an
already-split password set, producing TWO variants per split:

  A) sibling         -> adds "Siblings" only          (old passwords)
  B) sibling_account -> adds "Siblings" + "Account"   (old passwords + account name)

The ONLY difference from run_pcfg_combine_acc_sibling.py: Tokens/Tags are
generated on the fly with PagPassGPT structure tagging (char-class run-lengths
via tools.get_pattern, e.g. "love999!" -> Tokens "love|999!", Tags "L4|N3|S1")
instead of being read from semanticPCFG's semantic tags. There is therefore no
tagtype loop.

PII source (outside the project tree):
  /home/u4996812/passllm/data/{dataset}/{train,test}_addacc.json
  each row: {"Knowledge": {"Account": <str>, "Old password": [<str>, ...]}, "password": <str>}

Password + split source (the base rows; tags here are ignored and recomputed):
  {input_root}/{dataset}/{ref_tagtype}/split/{train,test}_data.jsonl

Join key: row index. Verified row-aligned by a full-scan Password/password
comparison (raises on any mismatch), identical to run_pcfg_combine_acc_sibling.py.

Output:
  {output_root}/combine_acc_sibling[_{dataset}]/sibling/split/{train,test}_data.jsonl
  {output_root}/combine_acc_sibling[_{dataset}]/sibling_account/split/{train,test}_data.jsonl
  (COMB_MIX keeps the un-suffixed name for parity; each variant holds a split/
  subdir, matching util/train.py:load_datasets())

Usage:
  python run_pagpass_combine_acc_sibling.py                   # dataset=COMB_MIX, both variants
  python run_pagpass_combine_acc_sibling.py --dataset Collection1_acc_pii
  python run_pagpass_combine_acc_sibling.py --sibling-limit 5 --force
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from run_pagpass_segment import load_config, get_segmenter, segment_and_tag

PROJECT_ROOT = Path(__file__).resolve().parent

# PassLLM PII lives outside the project tree (same constant as
# run_pcfg_combine_acc_sibling.py).
PASSLLM_DIR = Path("/home/u4996812/passllm/data")

_SPLIT_TO_PASSLLM_FILE = {"train": "train_addacc.json", "test": "test_addacc.json"}

# variant name -> whether to include the Account column
_VARIANTS = {
    "sibling": False,
    "sibling_account": True,
}


def out_root(dataset: str, output_root: Path) -> Path:
    """Namespace the output by dataset; COMB_MIX keeps the un-suffixed name."""
    if dataset == "COMB_MIX":
        return output_root / "combine_acc_sibling"
    return output_root / f"combine_acc_sibling_{dataset}"


def load_passllm(dataset: str, split_name: str) -> list:
    path = PASSLLM_DIR / dataset / _SPLIT_TO_PASSLLM_FILE[split_name]
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_pii_columns(tagged_df: pd.DataFrame, passllm_rows: list, sibling_limit: int):
    """Row-index join. Returns (siblings_col, account_col).

    Raises if the two sources disagree on row count or any Password value —
    a mismatch means the row-index join is unsafe.
    """
    if len(tagged_df) != len(passllm_rows):
        raise ValueError(
            f"Row count mismatch: tagged={len(tagged_df):,} vs passllm={len(passllm_rows):,}. "
            "Row-index join is unsafe — re-verify alignment before combining."
        )

    siblings_col, account_col = [], []
    for i, (tagged_pw, passllm_row) in enumerate(zip(tagged_df["Password"], passllm_rows)):
        if tagged_pw != passllm_row["password"]:
            raise ValueError(
                f"Password mismatch at row {i}: tagged={tagged_pw!r} vs passllm={passllm_row['password']!r}. "
                "Row-index join is unsafe — re-verify alignment before combining."
            )
        knowledge = passllm_row["Knowledge"]
        old_passwords = knowledge.get("Old password", [])[:sibling_limit]
        siblings_col.append(json.dumps(old_passwords, ensure_ascii=False))
        account_col.append(knowledge.get("Account") or "")

    return siblings_col, account_col


def retag(df: pd.DataFrame, get_pattern) -> pd.DataFrame:
    """Overwrite Tokens/Tags with PagPassGPT structure tags (in place)."""
    tokens_col, tags_col = [], []
    for pw in df["Password"].astype(str):
        tokens, tags = segment_and_tag(pw, get_pattern)
        tokens_col.append("|".join(tokens))
        tags_col.append("|".join(tags))
    df["Tokens"] = tokens_col
    df["Tags"]   = tags_col
    return df


def combine_split(dataset: str, split_name: str, cfg: dict, get_pattern,
                  sibling_limit: int, force: bool):
    tagged_path = (PROJECT_ROOT / cfg["input_root"] / dataset /
                   cfg["ref_tagtype"] / "split" / f"{split_name}_data.jsonl")
    output_root = PROJECT_ROOT / cfg["output_root"]

    tagged_df    = pd.read_json(tagged_path, orient="records", lines=True)
    passllm_rows = load_passllm(dataset, split_name)

    print(f"    Combining {len(tagged_df):,} {split_name} rows "
          f"(PagPassGPT tags, sibling_limit={sibling_limit}) ...")

    # Recompute Tokens/Tags with PagPassGPT, then build PII columns once.
    tagged_df = retag(tagged_df, get_pattern)
    siblings_col, account_col = build_pii_columns(tagged_df, passllm_rows, sibling_limit)

    with_siblings = sum(1 for s in siblings_col if s != "[]")
    with_account  = sum(1 for a in account_col if a)

    for variant, include_account in _VARIANTS.items():
        out_dir  = out_root(dataset, output_root) / variant / "split"
        out_path = out_dir / f"{split_name}_data.jsonl"

        if out_path.exists() and not force:
            print(f"      [skip] {variant}/{out_path.name} already exists (use --force to re-run)")
            continue

        df = tagged_df.copy()
        df["Siblings"] = siblings_col
        if include_account:
            df["Account"] = account_col

        out_dir.mkdir(parents=True, exist_ok=True)
        df.to_json(out_path, orient="records", lines=True, force_ascii=False)
        extra = f", {with_account:,} with Account" if include_account else ""
        print(f"      Saved {len(df):,} rows -> {out_path} "
              f"({with_siblings:,} with siblings{extra})")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Combine PassLLM sibling passwords + account with PagPassGPT structure tags "
                    "(two variants: sibling, sibling_account)"
    )
    parser.add_argument("--dataset", default="COMB_MIX", help="Dataset name (default: COMB_MIX)")
    parser.add_argument("--sibling-limit", type=int, default=5, help="Max sibling passwords per row (default: 5)")
    parser.add_argument("--force", action="store_true", help="Re-run even if the output already exists")
    return parser.parse_args()


def main():
    args = parse_args()
    cfg  = load_config()
    get_pattern = get_segmenter(cfg["pagpassgpt_root"])

    print(f"\n{'='*60}")
    print(f"dataset: {args.dataset}  |  variants: {', '.join(_VARIANTS)}  |  tags: PagPassGPT")
    print(f"{'='*60}")

    for split_name in ("train", "test"):
        combine_split(args.dataset, split_name, cfg, get_pattern,
                      args.sibling_limit, args.force)


if __name__ == "__main__":
    main()
