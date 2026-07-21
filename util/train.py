from functools import partial
from pathlib import Path
import json
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
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training

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
    lora_kind  = config.get("lora_kind", "lora")  # "lora" | "qlora"
    local_path = PROJECT_ROOT / tc["model_path"] / tc["model_name"]
    source     = str(local_path) if local_path.exists() else tc["model_name"]

    tokenizer  = AutoTokenizer.from_pretrained(source)

    if lora_kind == "qlora":
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        print(f"[*] QLoRA 模式：4-bit NF4 量化載入 {source}")
        model = AutoModelForCausalLM.from_pretrained(source, quantization_config=bnb_config)
    else:
        torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        print(f"[*] LoRA 模式：bf16 載入 {source}")
        model = AutoModelForCausalLM.from_pretrained(source, torch_dtype=torch_dtype)

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


def build_training_args(config: dict, run_dir: Path, train_size: int) -> TrainingArguments:
    import os
    tc = dict(config["train"]["train_config"])  # shallow copy to allow overrides
    if config.get("lora_kind") == "qlora":
        overrides = config.get("qlora_train_overrides", {})
        tc.update(overrides)
        print(f"[*] QLoRA overrides applied: {overrides}")

    # logging_dir 改用環境變數設定（transformers v5.2 移除 logging_dir 參數）
    tensorboard_dir = str(run_dir.parent / "runs" / run_dir.name)
    os.environ["TENSORBOARD_LOGGING_DIR"] = tensorboard_dir

    # warmup_ratio 改用 warmup_steps（transformers v5.2 移除 warmup_ratio 參數）
    steps_per_epoch = max(1, train_size // (tc["per_device_train_batch_size"] * tc["gradient_accumulation_steps"]))
    total_steps = steps_per_epoch * tc["num_train_epochs"]
    warmup_steps = max(1, int(total_steps * tc["warmup_ratio"]))
    print(f"[*] total_steps={total_steps}  warmup_steps={warmup_steps}")

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
        gradient_checkpointing=True,
        eval_on_start=False,
        label_smoothing_factor=tc["label_smoothing_factor"],
        dataloader_num_workers=tc.get("dataloader_num_workers", 2),
        push_to_hub=False,
    )


def train(config: dict = None, resume_from_checkpoint: str = None):
    if resume_from_checkpoint and "resume_from_checkpoint" not in (config or {}):
        config = dict(config or {})
        config["resume_from_checkpoint"] = resume_from_checkpoint
    if config is None:
        config = load_config()

    # 續訓：優先讀該 run 啟動當下存的 config 快照，避免中途改動
    # config/train_config.yaml（尤其 lora_config）導致 checkpoint 架構對不上。
    resume_ckpt = config.get("resume_from_checkpoint", None)
    if resume_ckpt:
        resume_ckpt = Path(resume_ckpt)
        if not resume_ckpt.is_absolute():
            resume_ckpt = PROJECT_ROOT / resume_ckpt
        if not resume_ckpt.exists():
            raise FileNotFoundError(
                f"[!] Checkpoint 不存在：{resume_ckpt}\n"
                f"    請確認路徑正確，或在 Colab 先從 Drive 還原 checkpoints。"
            )
        run_dir = resume_ckpt.parent
        print(f"[*] 繼續訓練，沿用目錄：{run_dir}  (from {resume_ckpt.name})")

        snapshot_path = run_dir / "train_config_snapshot.json"
        if snapshot_path.exists():
            with open(snapshot_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            print(f"[*] 讀取該 run 啟動時的參數快照：{snapshot_path}")
        else:
            print(
                f"[!] 找不到 {snapshot_path}（此 run 建立於快照機制之前），"
                f"將直接使用目前 config/train_config.yaml，請自行確認 LoRA 架構與當初一致。"
            )
    else:
        run_dir = None  # 新 run，等 base_dir 確定後再建立

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

    template_id = config["train"].get("prompt_template_id", 1)
    preprocess_fn = partial(
        process_train_targeted,
        prompt_ids=prompt_ids,
        vocab=vocab,
        tokenizer=tokenizer,
        max_length=512,
        template_id=template_id,
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

    lora_kind = config.get("lora_kind", "lora")
    if lora_kind == "qlora":
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = apply_lora(model, config["train"]["lora_config"])
    if lora_kind != "qlora":
        model.enable_input_require_grads()  # required for gradient_checkpointing + LoRA
    tc            = config["train"]["train_config"]

    if run_dir is None:
        base_dir = PROJECT_ROOT / tc["output_dir"] / tc["model_name"]
        base_dir.mkdir(parents=True, exist_ok=True)
        run_dir = _next_run_dir(base_dir)
        snapshot_path = run_dir / "train_config_snapshot.json"
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"[*] 已存參數快照：{snapshot_path}")

    training_args = build_training_args(config, run_dir, train_size=len(train_dataset))

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        processing_class=tokenizer,
    )

    trainer.train(resume_from_checkpoint=str(resume_ckpt) if resume_ckpt else None)

    lora_save_path = run_dir / "lora_final"
    model.save_pretrained(str(lora_save_path))
    print(f"LoRA weights saved to {lora_save_path}")


    