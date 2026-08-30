"""
run_pcfg_combine_multistruct.py

Combine the three per-tagtype PCFG-native tagged splits of the SAME dataset into a
single multi-structure dataset for prompt id=8 (multi-structcand; see docs/promt.md).

The three tagtype splits
  datasets/processed/semanticPCFG/{dataset}/{backoff,pos,pos_semantic}/split/{train,test}_data.jsonl
are row-aligned by Password (they were produced from the same account-ordered password
list by run_pcfg_segment.py — the same alignment run_pcfg_combine_sibling.py relies on).
This script joins them by row index, verifies the Password field matches across all three
(full scan, raises on any mismatch), and writes the PRIMARY tagtype's rows plus one new
column:

  "CandTags": a json.dumps'd list of the OTHER two tagtypes' pipe-joined tag strings
              (NOT inline <tag> form — prompt_convert_multi_structure / process_train_targeted
              build the "<tag>" inline structure at prompt-composition time, matching how
              id=5/id=7 store Tags and build inline later).

Primary tagtype = backoff; candidate tagtypes = [pos, pos_semantic] (order preserved).

Input:
  datasets/processed/semanticPCFG/{dataset}/{tagtype}/split/{train,test}_data.jsonl

Output:
  datasets/processed/semanticPCFG/{dataset}/multistruct/split/{train,test}_data.jsonl
  (split/ subdir matches util/train.py:load_datasets()'s fixed {dataset_path}/split/ layout)

Usage:
  python run_pcfg_combine_multistruct.py                 # dataset=COMB
  python run_pcfg_combine_multistruct.py --dataset COMB --force
"""

import argparse
import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
SPLIT_DIR    = PROJECT_ROOT / "datasets" / "processed" / "semanticPCFG"

PRIMARY_TAGTYPE    = "backoff"
CANDIDATE_TAGTYPES = ["pos", "pos_semantic"]  # order preserved in the CandTags list


def _split_path(dataset: str, tagtype: str, split_name: str) -> Path:
    return SPLIT_DIR / dataset / tagtype / "split" / f"{split_name}_data.jsonl"


def build_candtags_column(primary_df: pd.DataFrame, cand_dfs: list) -> list:
    """Row-index join across the primary + candidate tagtype frames.

    Raises if any frame disagrees with the primary on row count or Password value —
    a mismatch means the row-index join is unsafe and the datasets must be re-verified.
    """
    n = len(primary_df)
    for tt, df in zip(CANDIDATE_TAGTYPES, cand_dfs):
        if len(df) != n:
            raise ValueError(
                f"Row count mismatch: {PRIMARY_TAGTYPE}={n:,} vs {tt}={len(df):,}. "
                "Row-index join is unsafe — re-verify alignment before combining."
            )

    primary_pw = primary_df["Password"].tolist()
    cand_pw    = [df["Password"].tolist() for df in cand_dfs]
    cand_tags  = [df["Tags"].tolist() for df in cand_dfs]

    candtags_col = []
    for i in range(n):
        for tt, pw_list in zip(CANDIDATE_TAGTYPES, cand_pw):
            if pw_list[i] != primary_pw[i]:
                raise ValueError(
                    f"Password mismatch at row {i}: {PRIMARY_TAGTYPE}={primary_pw[i]!r} "
                    f"vs {tt}={pw_list[i]!r}. Row-index join is unsafe — re-verify alignment."
                )
        candtags_col.append(json.dumps([tags[i] for tags in cand_tags], ensure_ascii=False))

    return candtags_col


def combine_split(dataset: str, split_name: str, force: bool):
    primary_path = _split_path(dataset, PRIMARY_TAGTYPE, split_name)
    out_dir      = SPLIT_DIR / dataset / "multistruct" / "split"
    out_path     = out_dir / f"{split_name}_data.jsonl"

    if out_path.exists() and not force:
        print(f"    [skip] {out_path.name} already exists (use --force to re-run)")
        return

    primary_df = pd.read_json(primary_path, orient="records", lines=True)
    cand_dfs   = [
        pd.read_json(_split_path(dataset, tt, split_name), orient="records", lines=True)
        for tt in CANDIDATE_TAGTYPES
    ]

    print(f"    Combining {len(primary_df):,} {split_name} rows "
          f"(primary={PRIMARY_TAGTYPE}, candidates={CANDIDATE_TAGTYPES}) ...")
    primary_df["CandTags"] = build_candtags_column(primary_df, cand_dfs)

    out_dir.mkdir(parents=True, exist_ok=True)
    primary_df.to_json(out_path, orient="records", lines=True, force_ascii=False)
    print(f"    Saved {len(primary_df):,} rows -> {out_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Combine the 3 per-tagtype tagged splits into a multi-structure dataset (prompt id=8)"
    )
    parser.add_argument("--dataset", default="COMB", help="Tagged dataset name (default: COMB)")
    parser.add_argument("--force", action="store_true", help="Re-run combining even if the output already exists")
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"\n{'='*60}")
    print(f"dataset: {args.dataset}  (primary={PRIMARY_TAGTYPE}, candidates={CANDIDATE_TAGTYPES})")
    print(f"{'='*60}")

    for split_name in ("train", "test"):
        combine_split(args.dataset, split_name, args.force)


if __name__ == "__main__":
    main()
