"""
run_pcfg_segment.py

PCFG-native segmentation + tagging pipeline.

Stage A – Tagging  (per tagtype × dataset):
  Read cleaned passwords → PCFGSegmenter → save CSV
  Output: gen/semanticPCFG/{dataset}_{tagtype}_tagged.csv
  Columns: Password, Tokens, Tags

Stage B – Splitting (per tagtype, after all datasets are tagged):
  Load all dataset CSVs → filter → sample → train/test split → save JSONL
  Output: datasets/processed/semanticPCFG/{tagtype}/split/train_data.jsonl
          datasets/processed/semanticPCFG/{tagtype}/split/test_data.jsonl

Usage:
  python run_pcfg_segment.py                   # all tagtypes × all datasets
  python run_pcfg_segment.py --tagtype backoff # single tagtype only
  python run_pcfg_segment.py --force           # re-run even if CSV exists
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH  = PROJECT_ROOT / "config" / "pcfg_segment.yaml"


# ──────────────────────────────────────────────────────────────────────────────
# Config helpers
# ──────────────────────────────────────────────────────────────────────────────

def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ──────────────────────────────────────────────────────────────────────────────
# Stage A: tag one dataset with one tagtype
# ──────────────────────────────────────────────────────────────────────────────

def tag_dataset(
    segmenter,
    dataset: str,
    cfg: dict,
    force: bool = False,
) -> Path:
    """
    Segment + tag all cleaned passwords for *dataset* using *segmenter*.

    Returns the path to the saved CSV.
    """
    tagged_dir = PROJECT_ROOT / cfg["dirs"]["tagged"]
    tagged_dir.mkdir(parents=True, exist_ok=True)
    out_path = tagged_dir / f"{dataset}_{segmenter.tagtype}_tagged.csv"

    if out_path.exists() and not force:
        print(f"  [skip] {out_path.name} already exists (use --force to re-run)")
        return out_path

    # Load cleaned passwords
    cleaned_path = PROJECT_ROOT / cfg["dirs"]["datasets"] / dataset / "cleaned_data.txt"
    if not cleaned_path.exists():
        print(f"  [WARNING] cleaned data not found: {cleaned_path} — skipping")
        return None

    with open(cleaned_path, "r", encoding="utf-8", errors="ignore") as f:
        passwords = [line.rstrip("\r\n") for line in f if line.strip()]

    print(f"  Tagging {len(passwords):,} passwords from {dataset} ...")

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

        rows.append({
            "Password": pw,
            "Tokens":   "|".join(tokens),
            "Tags":     "|".join(tags),
        })

    if skipped:
        print(f"  [info] skipped {skipped:,} passwords (segmentation failed or empty)")

    df = pd.DataFrame(rows, columns=["Password", "Tokens", "Tags"])
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"  Saved {len(df):,} rows -> {out_path}")
    return out_path


# ──────────────────────────────────────────────────────────────────────────────
# Stage B: load all dataset CSVs for one tagtype, sample, split, save JSONL
# ──────────────────────────────────────────────────────────────────────────────

def split_tagtype(tagtype: str, cfg: dict) -> None:
    """
    Load all tagged CSVs for *tagtype*, filter by length, sample,
    split into train/test, save JSONL.
    """
    tagged_dir   = PROJECT_ROOT / cfg["dirs"]["tagged"]
    processed_dir = PROJECT_ROOT / cfg["dirs"]["processed"] / tagtype / "split"
    processed_dir.mkdir(parents=True, exist_ok=True)

    train_path = processed_dir / "train_data.jsonl"
    test_path  = processed_dir / "test_data.jsonl"

    # Load all dataset CSVs for this tagtype
    frames = []
    for dataset in cfg["datasets"]:
        csv_path = tagged_dir / f"{dataset}_{tagtype}_tagged.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df["source"] = dataset
            frames.append(df)
            print(f"  Loaded {len(df):,} rows from {csv_path.name}")
        else:
            print(f"  [WARNING] Not found: {csv_path.name} — skipping")

    if not frames:
        print(f"  [ERROR] No data found for tagtype={tagtype}, aborting split.")
        return

    df = pd.concat(frames, ignore_index=True)

    # Filter by password length
    min_len = cfg["password_filter"]["min_length"]
    max_len = cfg["password_filter"]["max_length"]
    before  = len(df)
    df = df[
        (df["Password"].str.len() >= min_len) &
        (df["Password"].str.len() <= max_len)
    ].reset_index(drop=True)
    print(f"  Length filter [{min_len},{max_len}]: {before:,} -> {len(df):,}")

    # Sample
    seed   = cfg["seed"]
    ratio  = cfg["expected_ratio"]
    n      = max(1, int(len(df) * ratio))
    df     = df.sample(n=n, random_state=seed).reset_index(drop=True)
    print(f"  Sampled {len(df):,} rows ({ratio:.0%} of filtered)")

    # Train / test split
    split_ratio = cfg["split_ratio"]
    test_df  = df.sample(frac=split_ratio, random_state=seed)
    train_df = df.drop(test_df.index).reset_index(drop=True)
    test_df  = test_df.reset_index(drop=True)

    train_df.to_json(train_path, orient="records", lines=True, force_ascii=False)
    test_df.to_json(test_path,   orient="records", lines=True, force_ascii=False)
    print(f"  Train: {len(train_df):,} rows -> {train_path}")
    print(f"  Test:  {len(test_df):,} rows  -> {test_path}")

    # Length distribution
    dist_path = processed_dir / "length_distribution.json"
    dist = {}
    for split_name, path in [("train", train_path), ("test", test_path)]:
        d = pd.read_json(path, lines=True)
        dist[split_name] = (
            d["Password"].dropna().str.len()
            .value_counts().sort_index().to_dict()
        )
    with open(dist_path, "w", encoding="utf-8") as f:
        json.dump(dist, f, ensure_ascii=False, indent=4)
    print(f"  Length distribution saved -> {dist_path}")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="PCFG-native segmentation + tagging pipeline"
    )
    parser.add_argument(
        "--tagtype",
        choices=["pos", "backoff", "pos_semantic"],
        default=None,
        help="Run only this tagtype (default: all tagtypes in config)",
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="Run only this dataset (default: all datasets in config)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run tagging even if the CSV already exists",
    )
    parser.add_argument(
        "--tag-only",
        action="store_true",
        help="Only run Stage A (tagging), skip Stage B (splitting)",
    )
    parser.add_argument(
        "--split-only",
        action="store_true",
        help="Only run Stage B (splitting) from existing CSVs",
    )
    return parser.parse_args()


def main():
    args   = parse_args()
    cfg    = load_config()
    force  = args.force or cfg.get("force_retag", False)

    tagtypes = [args.tagtype] if args.tagtype else cfg["tagtypes"]
    datasets = [args.dataset] if args.dataset else cfg["datasets"]

    sg_path = str(PROJECT_ROOT / cfg["semantic_guesser_path"])

    for tagtype in tagtypes:
        print(f"\n{'='*60}")
        print(f"tagtype: {tagtype}")
        print(f"{'='*60}")

        # ── Stage A: tag each dataset ─────────────────────────────
        if not args.split_only:
            # Import here so sys.path is set up once per tagtype
            # (PCFGSegmenter handles sys.path insertion internally)
            sys.path.insert(0, str(PROJECT_ROOT / "src"))
            from PCFGSegment import PCFGSegmenter

            segmenter = PCFGSegmenter(sg_path=sg_path, tagtype=tagtype)

            for dataset in datasets:
                print(f"\n  dataset: {dataset}")
                tag_dataset(segmenter, dataset, cfg, force=force)

        # ── Stage B: sample + split ───────────────────────────────
        if not args.tag_only:
            print(f"\n  --- Splitting for tagtype={tagtype} ---")
            split_tagtype(tagtype, cfg)


if __name__ == "__main__":
    main()
