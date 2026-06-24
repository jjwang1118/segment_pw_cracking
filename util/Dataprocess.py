
import os
import json
import yaml
import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH  = PROJECT_ROOT / "config" / "train_config.yaml"


def load_config(config_path: Path = CONFIG_PATH) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_tagged_data(config: dict) -> pd.DataFrame:
    """Load and concatenate tagged CSV files based on config."""
    seg_cfg   = config["segment_tag_path"]
    base_path = PROJECT_ROOT / seg_cfg["path"]
    kind      = seg_cfg["kind"]
    datasets  = seg_cfg["dataset"]

    frames = []
    for ds in datasets:
        filepath = base_path / f"{ds}_{kind}_tagged.csv"
        if filepath.exists():
            df = pd.read_csv(filepath)
            df["source"] = ds
            frames.append(df)
            print(f"Loaded {len(df):,} rows from {filepath.name}")
        else:
            print(f"[WARNING] Not found: {filepath}")

    if not frames:
        raise FileNotFoundError("No tagged data files found.")

    df = pd.concat(frames, ignore_index=True)
    before = len(df)
    df = df[(df["Password"].str.len() <= 20) & (df["Password"].str.len() >= 8)].reset_index(drop=True)
    print(f"Filtered by length <= 20: {before:,} -> {len(df):,} rows ({before - len(df):,} removed)")
    return df


def sample_data(df: pd.DataFrame, ratio: float, seed: int) -> pd.DataFrame:
    """Sample a fraction of rows."""
    n = max(1, int(len(df) * ratio))
    return df.sample(n=n, random_state=seed).reset_index(drop=True)


def split_train_test(df: pd.DataFrame, split_ratio: float, seed: int):
    """Split into train/test sets."""
    test_df  = df.sample(frac=split_ratio, random_state=seed)
    train_df = df.drop(test_df.index).reset_index(drop=True)
    test_df  = test_df.reset_index(drop=True)
    return train_df, test_df


if __name__ == "__main__":
    config = load_config()

    seed           = config["seed"]
    dataset_path   = PROJECT_ROOT / config["dataset_path"]
    expected_ratio = config["expected_ratio"]
    split_ratio    = config["split_ratio"]

    split_dir = dataset_path / "split"
    split_dir.mkdir(parents=True, exist_ok=True)

    train_path = split_dir / "train_data.jsonl"
    test_path  = split_dir / "test_data.jsonl"

    if train_path.exists() and test_path.exists():
        print("train/test files already exist, skipping.")
    else:
        print("Loading tagged data...")
        df = load_tagged_data(config)

        print(f"Sampling {expected_ratio:.4%} of {len(df):,} rows...")
        df = sample_data(df, expected_ratio, seed)

        print(f"Splitting {len(df):,} rows (test ratio={split_ratio})...")
        train_df, test_df = split_train_test(df, split_ratio, seed)

        train_df.to_json(train_path, orient="records", lines=True, force_ascii=False)
        test_df.to_json(test_path,   orient="records", lines=True, force_ascii=False)

        print(f"Train: {len(train_df):,} rows -> {train_path}")
        print(f"Test:  {len(test_df):,} rows  -> {test_path}")

    # Length distribution
    dist_path = split_dir / "length_distribution.json"
    if not dist_path.exists():
        print("Calculating length distribution...")
        dist = {}
        for split_name, path in [("train", train_path), ("test", test_path)]:
            df_split = pd.read_json(path, lines=True)
            dist[split_name] = (
                df_split["Password"].dropna().str.len()
                .value_counts().sort_index().to_dict()
            )

        with open(dist_path, "w", encoding="utf-8") as f:
            json.dump(dist, f, ensure_ascii=False, indent=4)
        print(f"Length distribution saved to {dist_path}")
