from functools import partial
from pathlib import Path
import torch
import yaml
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    DataCollatorForSeq2Seq,
    TrainingArguments,
    Trainer,
)
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, TaskType

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_config(config_path: Path = PROJECT_ROOT / "config" / "train_config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_datasets(config: dict):
    dataset_path = PROJECT_ROOT / config["dataset_path"] / "split"
    return load_dataset(
        "json",
        data_files={
            "train": str(dataset_path / "train_data.jsonl"),
            "test":  str(dataset_path / "test_data.jsonl"),
        },
    )


def build_model_and_tokenizer(config: dict):
    tc         = config["train"]["train_config"]
    local_path = PROJECT_ROOT / tc["model_path"] / tc["model_name"]
    source     = str(local_path) if local_path.exists() else tc["model_name"]

    tokenizer  = AutoTokenizer.from_pretrained(source)
    torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    model      = AutoModelForCausalLM.from_pretrained(source, torch_dtype=torch_dtype)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer


def apply_lora(model, lora_cfg: dict):
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"],
        init_lora_weights=lora_cfg["init_lora_weights"],
        target_modules=lora_cfg["target_modules"],
        bias=lora_cfg["bias"],
        lora_dropout=lora_cfg["lora_dropout"],
    )
    return get_peft_model(model, lora_config)


def _next_run_dir(base_dir: Path) -> Path:
    """Return checkpoints/{model}/run_N where N is the next available integer."""
    existing = [d.name for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
    nums = [int(d.split("_")[1]) for d in existing if d.split("_")[1].isdigit()]
    next_n = max(nums, default=0) + 1
    run_dir = base_dir / f"run_{next_n}"
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] 訓練輸出目錄：{run_dir}")
    return run_dir


def build_training_args(config: dict, run_dir: Path) -> TrainingArguments:
    tc = config["train"]["train_config"]
    return TrainingArguments(
        output_dir=str(run_dir),
        num_train_epochs=tc["num_train_epochs"],
        per_device_train_batch_size=tc["per_device_train_batch_size"],
        per_device_eval_batch_size=tc["per_device_eval_batch_size"],
        gradient_accumulation_steps=tc["gradient_accumulation_steps"],
        eval_strategy=tc["eval_strategy"],
        eval_steps=tc["eval_steps"],
        save_strategy="steps",
        save_steps=tc["save_steps"],
        logging_steps=tc["logging_steps"],
        save_total_limit=5,
        logging_dir=str(run_dir.parent / "runs" / run_dir.name),
        report_to="tensorboard",
        bf16=tc["bf16"] if torch.cuda.is_available() else False,
        seed=tc["seed"],
        data_seed=tc["data_seed"],
        learning_rate=float(tc["learning_rate"]),
        weight_decay=tc["weight_decay"],
        warmup_ratio=tc["warmup_ratio"],
        optim=tc["optim"],
        gradient_checkpointing=True,
        eval_on_start=True,
        label_smoothing_factor=tc["label_smoothing_factor"],
        dataloader_num_workers=4,
        push_to_hub=False,
    )


def train(config: dict = None):
    if config is None:
        config = load_config()

    from src.prompt_template import _get_indice
    from util.pw_tokenize import process_train_targeted, get_alpa

    prompt_template  = _get_indice(config["train"]["prompt_template_id"])
    datasets         = load_datasets(config)
    model, tokenizer = build_model_and_tokenizer(config)
    vocab            = get_alpa(tokenizer)

    # Pre-compute prompt_ids once — avoid re-tokenising the same string for every sample
    prompt_ids = tokenizer(prompt_template, add_special_tokens=False)["input_ids"]
    if tokenizer.bos_token_id is not None:
        prompt_ids = [tokenizer.bos_token_id] + prompt_ids

    preprocess_fn = partial(
        process_train_targeted,
        prompt_ids=prompt_ids,
        vocab=vocab,
        tokenizer=tokenizer,
        max_length=512,
    )

    train_dataset = datasets["train"].map(
        preprocess_fn, batched=True, batch_size=256,
        remove_columns=datasets["train"].column_names,
    )
    eval_dataset = datasets["test"].map(
        preprocess_fn, batched=True, batch_size=256,
        remove_columns=datasets["test"].column_names,
    )

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer, label_pad_token_id=-100, padding=True
    )

    model         = apply_lora(model, config["train"]["lora_config"])
    model.enable_input_require_grads()  # required for gradient_checkpointing + LoRA
    tc            = config["train"]["train_config"]
    base_dir      = PROJECT_ROOT / tc["output_dir"] / tc["model_name"]
    base_dir.mkdir(parents=True, exist_ok=True)
    run_dir       = _next_run_dir(base_dir)
    training_args = build_training_args(config, run_dir)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        processing_class=tokenizer,
    )

    trainer.train()

    lora_save_path = run_dir / "lora_final"
    model.save_pretrained(str(lora_save_path))
    print(f"LoRA weights saved to {lora_save_path}")


    