"""
run_pagpass_segment.py

PagPassGPT structure-tag pipeline.

Reads the already-split semanticPCFG JSONL (for the Password column + the
train/test membership) and recomputes Tokens/Tags per row using PagPassGPT's
structure tagging (char-class run-lengths via tools.get_pattern), then writes
a parallel PagPassGPT/ tree. The password set and split are left untouched, so
results are directly comparable to semanticPCFG.

PagPassGPT structure tag (deterministic, 1:1 with the password):
  L = letters, N = digits, S = symbols
  "love999!" -> Tags "L4|N3|S1", Tokens "love|999|!"

Input (per dataset, both splits):
  {input_root}/{dataset}/{ref_tagtype}/split/{train,test}_data.jsonl

Output:
  {output_root}/{dataset}/split/{train,test}_data.jsonl
  {output_root}/{dataset}/split/length_distribution.json
  (split/ subdir matches util/train.py:load_datasets()'s fixed layout)

All non-tag columns (Password, source, and anything else like Siblings /
Account) are preserved as-is; only Tokens and Tags are overwritten.

Usage:
  python run_pagpass_segment.py                   # all datasets in config
  python run_pagpass_segment.py --dataset rockyou-75
  python run_pagpass_segment.py --force           # re-run even if output exists
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH  = PROJECT_ROOT / "config" / "pagpass_segment.yaml"


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_segmenter(pagpassgpt_root: str):
    """Import PagPassGPT's get_pattern (reused from its tools/ package)."""
    root = str(Path(pagpassgpt_root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    from tools.password_pattern import get_pattern  # noqa: E402
    return get_pattern


def segment_and_tag(password: str, get_pattern) -> tuple:
    """Return (tokens, tags) for *password* using PagPassGPT structure tags.

    tags are char-class run-lengths (e.g. ['L4','N3','S1']); tokens slice the
    password to match those run-lengths (e.g. ['love','999','!']).
    """
    tags = get_pattern(password)
    tokens, pos = [], 0
    for tag in tags:
        n = int(tag[1:])
        tokens.append(password[pos:pos + n])
        pos += n
    return tokens, tags


def process_split(dataset: str, split_name: str, cfg: dict, get_pattern, force: bool) -> Path:
    pw_field = cfg["password_field"]
    in_path  = (PROJECT_ROOT / cfg["input_root"] / dataset /
                cfg["ref_tagtype"] / "split" / f"{split_name}_data.jsonl")
    out_dir  = PROJECT_ROOT / cfg["output_root"] / dataset / "split"
    out_path = out_dir / f"{split_name}_data.jsonl"

    if not in_path.exists():
        print(f"    [WARNING] input not found: {in_path} — skipping")
        return None

    if out_path.exists() and not force:
        print(f"    [skip] {split_name}_data.jsonl already exists (use --force to re-run)")
        return out_path

    df = pd.read_json(in_path, orient="records", lines=True)
    print(f"    Re-tagging {len(df):,} {split_name} rows from {dataset} ...")

    tokens_col, tags_col = [], []
    for pw in df[pw_field].astype(str):
        tokens, tags = segment_and_tag(pw, get_pattern)
        tokens_col.append("|".join(tokens))
        tags_col.append("|".join(tags))

    # Overwrite Tokens/Tags in place; preserve all other columns + order.
    df["Tokens"] = tokens_col
    df["Tags"]   = tags_col

    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_json(out_path, orient="records", lines=True, force_ascii=False)
    print(f"    Saved {len(df):,} rows -> {out_path}")
    return out_path


def write_length_distribution(dataset: str, cfg: dict) -> None:
    out_dir   = PROJECT_ROOT / cfg["output_root"] / dataset / "split"
    dist_path = out_dir / "length_distribution.json"
    pw_field  = cfg["password_field"]

    dist = {}
    for split_name in ("train", "test"):
        path = out_dir / f"{split_name}_data.jsonl"
        if not path.exists():
            continue
        d = pd.read_json(path, orient="records", lines=True)
        dist[split_name] = (
            d[pw_field].dropna().astype(str).str.len()
            .value_counts().sort_index().to_dict()
        )

    if dist:
        with open(dist_path, "w", encoding="utf-8") as f:
            json.dump(dist, f, ensure_ascii=False, indent=4)
        print(f"    Length distribution saved -> {dist_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="PagPassGPT structure-tag pipeline (re-tag semanticPCFG splits)"
    )
    parser.add_argument(
        "--dataset", default=None,
        help="Run only this dataset (default: all datasets in config)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-run even if the output JSONL already exists",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    cfg  = load_config()
    force = args.force or cfg.get("force", False)

    get_pattern = get_segmenter(cfg["pagpassgpt_root"])
    datasets = [args.dataset] if args.dataset else cfg["datasets"]

    for dataset in datasets:
        print(f"\n{'='*60}")
        print(f"dataset: {dataset}")
        print(f"{'='*60}")
        for split_name in ("train", "test"):
            process_split(dataset, split_name, cfg, get_pattern, force=force)
        write_length_distribution(dataset, cfg)


if __name__ == "__main__":
    main()
