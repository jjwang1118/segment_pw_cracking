import argparse
from util.train import load_config, train

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--resume", type=str, default=None,
        metavar="CHECKPOINT_DIR",
        help="從指定 checkpoint 繼續訓練，例如 checkpoints/Llama-3.2-3B-Instruct/run_4/checkpoint-800"
    )
    args = parser.parse_args()
    config = load_config()
    train(config, resume_from_checkpoint=args.resume)
