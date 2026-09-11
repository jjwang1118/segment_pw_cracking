"""
run_pcfg_combine_acc_sibling.py

Combine PassLLM PII (sibling passwords + account name) with the PCFG-native
tagged COMB_MIX dataset, producing TWO variants per split:

  A) sibling         -> adds "Siblings" only          (old passwords)
  B) sibling_account -> adds "Siblings" + "Account"   (old passwords + account name)

PII source (outside the project tree):
  /home/u4996812/passllm/data/{dataset}/{train,test}_addacc.json
  each row: {"Knowledge": {"Account": <str>, "Old password": [<str>, ...]}, "password": <str>}

Tagged source (PCFG-native, already processed):
  datasets/processed/semanticPCFG/{dataset}/{tagtype}/split/{train,test}_data.jsonl

Join key: row index. Verified row-aligned by a full-scan Password/password
comparison (raises on any mismatch), the same approach as
run_pcfg_combine_sibling.py. COMB_MIX train/test: 378,719 / 7,466 rows,
0 mismatches, 100% Account + Old-password coverage (verified 2026-09-11).

"Siblings": a json.dumps'd list of at most --sibling-limit prior passwords
(json, not pipe-joined, so siblings containing '|' survive intact — see
docs/promt.md id=7). Empty list "[]" when the account has none.
"Account": the raw account-name string ("" when absent).

Output:
  datasets/processed/semanticPCFG/combine_acc_sibling/sibling/{tagtype}/split/{train,test}_data.jsonl
  datasets/processed/semanticPCFG/combine_acc_sibling/sibling_account/{tagtype}/split/{train,test}_data.jsonl
  (each variant/tagtype dir holds a split/ subdir, matching util/train.py:load_datasets())

Usage:
  python run_pcfg_combine_acc_sibling.py                       # dataset=COMB_MIX, all tagtypes, both variants
  python run_pcfg_combine_acc_sibling.py --tagtype backoff
  python run_pcfg_combine_acc_sibling.py --sibling-limit 5 --force
"""

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH  = PROJECT_ROOT / "config" / "pcfg_segment.yaml"

# PassLLM PII lives outside the project tree (datasets/passllm/ is gitignored
# and not used for COMB_MIX; the *_addacc.json files carry both Account + Old password).
PASSLLM_DIR  = Path("/home/u4996812/passllm/data")
SPLIT_DIR    = PROJECT_ROOT / "datasets" / "processed" / "semanticPCFG"
OUT_DIR      = SPLIT_DIR / "combine_acc_sibling"

_SPLIT_TO_PASSLLM_FILE = {"train": "train_addacc.json", "test": "test_addacc.json"}

# variant name -> whether to include the Account column
_VARIANTS = {
    "sibling": False,
    "sibling_account": True,
}


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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


def combine_split(dataset: str, tagtype: str, split_name: str, sibling_limit: int, force: bool):
    tagged_path  = SPLIT_DIR / dataset / tagtype / "split" / f"{split_name}_data.jsonl"

    # Compute the PII columns once; reuse across both variants.
    tagged_df    = pd.read_json(tagged_path, orient="records", lines=True)
    passllm_rows = load_passllm(dataset, split_name)

    print(f"    Combining {len(tagged_df):,} {split_name} rows "
          f"(tagtype={tagtype}, sibling_limit={sibling_limit}) ...")
    siblings_col, account_col = build_pii_columns(tagged_df, passllm_rows, sibling_limit)

    with_siblings = sum(1 for s in siblings_col if s != "[]")
    with_account  = sum(1 for a in account_col if a)

    for variant, include_account in _VARIANTS.items():
        out_dir  = OUT_DIR / variant / tagtype / "split"
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
        description="Combine PassLLM sibling passwords + account with PCFG-native COMB_MIX "
                    "(two variants: sibling, sibling_account)"
    )
    parser.add_argument("--dataset", default="COMB_MIX", help="Tagged dataset name (default: COMB_MIX)")
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
    print(f"dataset: {args.dataset}  |  variants: {', '.join(_VARIANTS)}")
    print(f"{'='*60}")

    for tagtype in tagtypes:
        print(f"\n  tagtype: {tagtype}")
        for split_name in ("train", "test"):
            combine_split(args.dataset, tagtype, split_name, args.sibling_limit, args.force)


if __name__ == "__main__":
    main()
