"""
run_pcfg_combine_sibling.py

Combine sibling-password info (datasets/passllm/{TRAIN,TEST}.json,
Knowledge."Old password") with the PCFG-native tagged COMB dataset
(datasets/processed/semanticPCFG/{dataset}/{tagtype}/split/{train,test}_data.jsonl)
for prompt id=7 (see docs/promt.md).

Join key: row index. datasets/passllm/{TRAIN,TEST}.json and the PCFG-native
COMB split files were built from the same account-ordered password list —
verified by a full-scan Password-field comparison (0 mismatches across
262,263 train / 13,513 test rows for every tagtype).

Output adds a "Siblings" column: a json.dumps'd list of at most
--sibling-limit prior passwords for the same account (json, not pipe-joined,
so sibling passwords containing '|' don't need to be filtered out — see
docs/promt.md id=7 and docs/reports/comparison_PassLLM_vs_PCFG-LLM_COMB.md
section 7, which found PassLLM's JSON-wrapped "Old password" format
outperformed a '</s>'-joined format). Empty list "[]" when the account has
no sibling passwords.

Input:
  datasets/passllm/{TRAIN,TEST}.json
  datasets/processed/semanticPCFG/{dataset}/{tagtype}/split/{train,test}_data.jsonl

Output:
  datasets/processed/semanticPCFG/combine/{tagtype}/split/{train,test}_data.jsonl
  (split/ subdir matches util/train.py:load_datasets()'s fixed {dataset_path}/split/ layout)

Usage:
  python run_pcfg_combine_sibling.py                  # dataset=COMB, all tagtypes
  python run_pcfg_combine_sibling.py --tagtype backoff
  python run_pcfg_combine_sibling.py --sibling-limit 5 --force
"""

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH  = PROJECT_ROOT / "config" / "pcfg_segment.yaml"

PASSLLM_DIR  = PROJECT_ROOT / "datasets" / "passllm"
SPLIT_DIR    = PROJECT_ROOT / "datasets" / "processed" / "semanticPCFG"
COMBINE_DIR  = PROJECT_ROOT / "datasets" / "processed" / "semanticPCFG" / "combine"

_SPLIT_TO_PASSLLM_FILE = {"train": "TRAIN.json", "test": "TEST.json"}


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_passllm(split_name: str) -> list:
    path = PASSLLM_DIR / _SPLIT_TO_PASSLLM_FILE[split_name]
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_siblings_column(tagged_df: pd.DataFrame, passllm_rows: list, sibling_limit: int) -> list:
    """Row-index join. Raises if the two sources disagree on a Password value."""
    if len(tagged_df) != len(passllm_rows):
        raise ValueError(
            f"Row count mismatch: tagged={len(tagged_df):,} vs passllm={len(passllm_rows):,}. "
            "Row-index join is unsafe — re-verify alignment before combining."
        )

    siblings_col = []
    for i, (tagged_pw, passllm_row) in enumerate(zip(tagged_df["Password"], passllm_rows)):
        if tagged_pw != passllm_row["password"]:
            raise ValueError(
                f"Password mismatch at row {i}: tagged={tagged_pw!r} vs passllm={passllm_row['password']!r}. "
                "Row-index join is unsafe — re-verify alignment before combining."
            )
        old_passwords = passllm_row["Knowledge"]["Old password"][:sibling_limit]
        siblings_col.append(json.dumps(old_passwords, ensure_ascii=False))

    return siblings_col


def combine_split(dataset: str, tagtype: str, split_name: str, sibling_limit: int, force: bool):
    tagged_path = SPLIT_DIR / dataset / tagtype / "split" / f"{split_name}_data.jsonl"
    out_dir     = COMBINE_DIR / tagtype / "split"
    out_path    = out_dir / f"{split_name}_data.jsonl"

    if out_path.exists() and not force:
        print(f"    [skip] {out_path.name} already exists (use --force to re-run)")
        return

    tagged_df = pd.read_json(tagged_path, orient="records", lines=True)
    passllm_rows = load_passllm(split_name)

    print(f"    Combining {len(tagged_df):,} {split_name} rows "
          f"(tagtype={tagtype}, sibling_limit={sibling_limit}) ...")
    tagged_df["Siblings"] = build_siblings_column(tagged_df, passllm_rows, sibling_limit)

    out_dir.mkdir(parents=True, exist_ok=True)
    tagged_df.to_json(out_path, orient="records", lines=True, force_ascii=False)

    with_siblings = sum(1 for s in tagged_df["Siblings"] if s != "[]")
    print(f"    Saved {len(tagged_df):,} rows -> {out_path} "
          f"({with_siblings:,} rows with sibling passwords, "
          f"{with_siblings / len(tagged_df):.1%})")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Combine sibling-password info with PCFG-native tagged COMB dataset (prompt id=7)"
    )
    parser.add_argument("--dataset", default="COMB", help="Tagged dataset name (default: COMB)")
    parser.add_argument(
        "--tagtype", choices=["pos", "backoff", "pos_semantic"], default=None,
        help="Run only this tagtype (default: all tagtypes in pcfg_segment.yaml)",
    )
    parser.add_argument("--sibling-limit", type=int, default=5, help="Max sibling passwords per row (default: 5)")
    parser.add_argument("--force", action="store_true", help="Re-run combining even if the output already exists")
    return parser.parse_args()


def main():
    args = parse_args()
    cfg  = load_config()

    tagtypes = [args.tagtype] if args.tagtype else cfg["tagtypes"]

    print(f"\n{'='*60}")
    print(f"dataset: {args.dataset}")
    print(f"{'='*60}")

    for tagtype in tagtypes:
        print(f"\n  tagtype: {tagtype}")
        for split_name in ("train", "test"):
            combine_split(args.dataset, tagtype, split_name, args.sibling_limit, args.force)


if __name__ == "__main__":
    main()
