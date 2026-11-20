"""
階段一：純 plaintext「無條件分布學習」全參數微調 (full fine-tune, 不使用 LoRA)
────────────────────────────────────────────────────────────────────────────
目標：讓模型學到大量密碼的無條件分布 p(password)。
  目標函數 = causal-LM cross-entropy (MLE)，loss 覆蓋整串密碼 + eos
  （無條件生成，不做任何 label 遮罩）。

資料：datasets/processed/plaintext/split/{train,test}_data.jsonl
  每行 {"Password": "..."}。

輸出：
  - 訓練 checkpoint： <output_dir>/<model_name>-plaintext/run_N/
  - 階段一最終模型： <model_path>/<model_name>-plaintext/run_N/
                     （供階段二 run_train.py 以 model_path=<...>/models、
                       model_name=<model_name>-plaintext/run_N 引用）

用法：
  python run_train_plaintext.py --config config/train_plaintext.yaml
  # 續訓：
  python run_train_plaintext.py --resume <output_dir>/<model_name>-plaintext/run_N/checkpoint-XXXX
"""
import argparse
from pathlib import Path

import torch
import yaml
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    DataCollatorForSeq2Seq,
    TrainingArguments,
    Trainer,
)

PROJECT_ROOT = Path(__file__).resolve().parent


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_plaintext_datasets(config: dict):
    """讀 datasets/processed/plaintext/split/{train,test}_data.jsonl（每行 {"Password": ...}）。"""
    dataset_path = PROJECT_ROOT / config["dataset_path"] / "split"
    return load_dataset(
        "json",
        data_files={
            "train": str(dataset_path / "train_data.jsonl"),
            "test":  str(dataset_path / "test_data.jsonl"),
        },
    )


def build_model_and_tokenizer(tc: dict):
    """全參數微調：以 bf16 載入 base LLM（無量化、無 LoRA）。"""
    local_path = PROJECT_ROOT / tc["model_path"] / tc["model_name"]
    source = str(local_path) if local_path.exists() else tc["model_name"]

    tokenizer = AutoTokenizer.from_pretrained(source)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    print(f"[*] 全參數微調：bf16 載入 {source}")
    model = AutoModelForCausalLM.from_pretrained(source, torch_dtype=torch_dtype)
    return model, tokenizer


def _next_run_dir(base_dir: Path) -> Path:
    """回傳 <base_dir>/run_N，N 取現有最大值 +1。"""
    base_dir.mkdir(parents=True, exist_ok=True)
    existing = [d.name for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
    nums = [int(d.split("_")[1]) for d in existing if d.split("_")[1].isdigit()]
    next_n = max(nums, default=0) + 1
    run_dir = base_dir / f"run_{next_n}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _resolve_run_dir(tc: dict, resume: str | None) -> tuple[Path, int]:
    """決定 checkpoint 輸出目錄與 run 編號。
    續訓：沿用 resume checkpoint 的 run_N 目錄；否則在 <output_dir>/<model>-plaintext 下開新的 run_N。
    """
    ckpt_base = PROJECT_ROOT / tc["output_dir"] / f'{tc["model_name"]}-plaintext'
    if resume:
        run_dir = Path(resume).resolve().parent  # .../run_N/checkpoint-XXXX -> .../run_N
    else:
        run_dir = _next_run_dir(ckpt_base)
    run_n = int(run_dir.name.split("_")[1])
    print(f"[*] 訓練輸出目錄：{run_dir}  (run_{run_n})")
    return run_dir, run_n


def tokenize_dataset(datasets, tokenizer, max_length: int):
    """密碼字串 -> input_ids（bos + 密碼 token + eos）；labels = input_ids（整串都算 loss）。"""
    eos_id = tokenizer.eos_token_id

    def _tok(batch):
        enc = tokenizer(
            batch["Password"],
            truncation=True,
            max_length=max_length - 1,   # 預留 1 格給手動補上的 eos
            add_special_tokens=True,     # Mistral 會自動加 bos；eos 下方手動補
        )
        input_ids = [ids + [eos_id] for ids in enc["input_ids"]]
        return {
            "input_ids": input_ids,
            "attention_mask": [[1] * len(x) for x in input_ids],
            "labels": [list(x) for x in input_ids],
        }

    remove_cols = datasets["train"].column_names
    return datasets.map(_tok, batched=True, remove_columns=remove_cols, desc="tokenize plaintext")


def build_training_args(tc: dict, run_dir: Path, train_size: int) -> TrainingArguments:
    import os

    # TensorBoard 目錄以環境變數設定（transformers v5.2 移除 logging_dir 參數）
    os.environ["TENSORBOARD_LOGGING_DIR"] = str(run_dir.parent / "runs" / run_dir.name)

    # warmup_ratio -> warmup_steps（transformers v5.2 移除 warmup_ratio 參數）
    eff_batch = tc["per_device_train_batch_size"] * tc["gradient_accumulation_steps"]
    steps_per_epoch = max(1, train_size // eff_batch)
    total_steps = steps_per_epoch * tc["num_train_epochs"]
    warmup_steps = max(1, int(total_steps * tc["warmup_ratio"]))
    print(f"[*] total_steps≈{total_steps}  warmup_steps={warmup_steps}")

    gc = tc.get("gradient_checkpointing", False)
    return TrainingArguments(
        output_dir=str(run_dir),
        num_train_epochs=tc["num_train_epochs"],
        per_device_train_batch_size=tc["per_device_train_batch_size"],
        per_device_eval_batch_size=tc["per_device_eval_batch_size"],
        gradient_accumulation_steps=tc["gradient_accumulation_steps"],
        eval_strategy=tc["eval_strategy"],
        eval_steps=tc["eval_steps"],
        eval_delay=tc.get("eval_delay", 0),
        save_strategy="steps",
        save_steps=tc["save_steps"],
        save_total_limit=tc.get("save_total_limit", 5),
        logging_steps=tc["logging_steps"],
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="tensorboard",
        bf16=tc["bf16"] if torch.cuda.is_available() else False,
        seed=tc["seed"],
        data_seed=tc["data_seed"],
        learning_rate=float(tc["learning_rate"]),
        weight_decay=tc["weight_decay"],
        warmup_steps=warmup_steps,
        optim=tc["optim"],
        gradient_checkpointing=gc,
        label_smoothing_factor=tc.get("label_smoothing_factor", 0),
        dataloader_num_workers=tc.get("dataloader_num_workers", 2),
        eval_on_start=False,
        push_to_hub=False,
    )


def main():
    parser = argparse.ArgumentParser(description="階段一：純 plaintext 無條件分布全參數微調")
    parser.add_argument(
        "--config", type=str, default=str(PROJECT_ROOT / "config" / "train_plaintext.yaml"),
        help="設定檔路徑（預設 config/train_plaintext.yaml）",
    )
    parser.add_argument(
        "--resume", type=str, default=None, metavar="CHECKPOINT_DIR",
        help="從指定 checkpoint 續訓，例如 <output_dir>/<model>-plaintext/run_N/checkpoint-XXXX",
    )
    args = parser.parse_args()

    config = load_config(Path(args.config))
    tc = config["train"]["train_config"]

    # 1) 模型 + tokenizer（全參數、bf16）
    model, tokenizer = build_model_and_tokenizer(tc)
    if tc.get("gradient_checkpointing", False):
        model.config.use_cache = False
        model.gradient_checkpointing_enable()

    # 2) 資料 -> tokenize（整串算 loss）
    datasets = load_plaintext_datasets(config)
    tokenized = tokenize_dataset(datasets, tokenizer, max_length=tc.get("max_length", 48))

    # 3) 輸出目錄 / run 編號
    run_dir, run_n = _resolve_run_dir(tc, args.resume)

    # 4) TrainingArguments + Trainer
    training_args = build_training_args(tc, run_dir, train_size=len(tokenized["train"]))
    collator = DataCollatorForSeq2Seq(tokenizer, label_pad_token_id=-100, padding=True)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"],
        data_collator=collator,
        processing_class=tokenizer,
    )

    # 5) 訓練（load_best_model_at_end=True：結束時 in-memory 模型 = eval_loss 最佳 checkpoint）
    trainer.train(resume_from_checkpoint=args.resume)

    # 6) 存階段一最終模型到 <model_path>/<model_name>-plaintext/run_N/（供階段二引用）
    final_dir = PROJECT_ROOT / tc["model_path"] / f'{tc["model_name"]}-plaintext' / f"run_{run_n}"
    final_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))
    print(f"[✓] 階段一最終模型已存：{final_dir}")


if __name__ == "__main__":
    main()
