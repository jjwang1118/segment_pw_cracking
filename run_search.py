"""
run_search.py — password generation entry point
Reads config/search.yaml and dispatches to the configured search method.

Usage:
    python run_search.py
    python run_search.py --config config/search.yaml
"""

import sys
import yaml
import json
import time
import torch
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def _load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_model_path(cfg):
    """Return model path from cfg['model_path'], or fall back to train_config.yaml."""
    if "model_path" in cfg:
        return str(PROJECT_ROOT / cfg["model_path"])
    train_cfg = _load_yaml(PROJECT_ROOT / "config" / "train_config.yaml")
    tc = train_cfg["train"]["train_config"]
    return str(PROJECT_ROOT / tc["model_path"] / tc["model_name"])


def _load_model(model_path, precision):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        dtype = {"half": torch.float16, "bf16": torch.bfloat16}.get(precision, torch.float32)
    else:
        dtype = torch.float32

    print(f"[*] 載入模型：{model_path}  (device={device}, dtype={dtype})")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=dtype)
    model.to(device)
    model.eval()
    return model, tokenizer, device


# ── Search method handlers ────────────────────────────────────────────────────

def run_contrastive_search(cfg):
    from util.search import contrastive_search
    from util.pw_tokenize import get_alpa, get_alpa_with_newline
    from src.prompt_template import _get_indice

    model_path = _resolve_model_path(cfg)
    precision = cfg.get("precistion", "full")  # key name preserved from yaml
    model, tokenizer, device = _load_model(model_path, precision)

    template_id = cfg.get("prompt_template_id", 0)
    vocab_dict = get_alpa_with_newline(tokenizer) if template_id == 4 else get_alpa(tokenizer)
    eos_id = tokenizer.eos_token_id
    newline_id = tokenizer('\n', add_special_tokens=False)['input_ids'][-1] if template_id == 4 else None
    if cfg.get("vocab_limit", True):
        exclude = {tokenizer.eos_token, "\t", "<", "|", ">"}
        char_ids = [v for k, v in vocab_dict.items() if k not in exclude]
        vocab_list = char_ids + ([newline_id] if newline_id is not None else []) + [eos_id]
    else:
        vocab_list = list(range(tokenizer.vocab_size - 1)) + [eos_id]

    # Prompt
    prompt_text = _get_indice(template_id)
    input_ids = tokenizer(
        prompt_text, return_tensors="pt", add_special_tokens=True
    )["input_ids"]

    # Beam / search width lists — make copies since contrastive_search mutates them
    beam_width = list(cfg["beam_width"])
    search_width_cfg = cfg.get("search_width", None)
    if search_width_cfg is None:
        search_width = beam_width[:]
    elif isinstance(search_width_cfg, int):
        search_width = [search_width_cfg] * len(beam_width)
    else:
        search_width = list(search_width_cfg)

    batch_size = cfg.get("batch_size", 1000)
    eos_threshold = cfg.get("eos_threshold", 0.001)
    max_guess = cfg.get("max_guess_number", None)
    min_len = cfg.get("min_len", 0)
    alpha = cfg.get("contrastive_alpha", 0.6)
    use_contrastive = cfg.get("use_contrastive", True)

    print(
        f"[*] 搜索參數：beam_width[0]={beam_width[0]}, max_length={len(beam_width)}, "
        f"batch_size={batch_size}, eos_threshold={eos_threshold}, "
        f"contrastive={'on' if use_contrastive else 'off'}"
    )

    start_time = time.time()
    results = contrastive_search(
        model=model,
        input_ids=input_ids,
        batch_size=batch_size,
        beam_width_list=beam_width,
        vocab=vocab_list,
        eos_threshold=eos_threshold,
        search_width_list=search_width,
        use_contrastive=use_contrastive,
        contrastive_alpha=alpha,
        min_len=min_len,
        seg_separator_id=newline_id,
    )
    elapsed = time.time() - start_time

    if max_guess:
        results = results[:max_guess]

    print(f"[*] 完成：找到 {len(results)} 個候選，耗時 {elapsed:.2f}s")

    # Save results as JSONL
    output_dir = PROJECT_ROOT / cfg.get("output_path", "gen")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / cfg.get("output_file_name", "search_results.jsonl")

    with open(output_file, "w", encoding="utf-8") as f:
        for seq, prob in results:
            decoded = tokenizer.decode(seq.tolist(), skip_special_tokens=True)
            if len(decoded) < min_len:
                continue
            f.write(json.dumps({"password": decoded, "log_prob": prob.item()}, ensure_ascii=False) + "\n")

    print(f"[*] 結果已儲存至 {output_file}")


def run_dynamic_beam_search(cfg):
    from util.search import dynamic_beam_search
    from util.pw_tokenize import get_alpa, get_alpa_with_newline
    from src.prompt_template import _get_indice

    model_path = _resolve_model_path(cfg)
    precision = cfg.get("precistion", "full")
    model, tokenizer, device = _load_model(model_path, precision)

    template_id = cfg.get("prompt_template_id", 0)
    vocab_dict = get_alpa_with_newline(tokenizer) if template_id == 4 else get_alpa(tokenizer)
    eos_id = tokenizer.eos_token_id
    newline_id = tokenizer('\n', add_special_tokens=False)['input_ids'][-1] if template_id == 4 else None
    if cfg.get("vocab_limit", True):
        exclude = {tokenizer.eos_token, "\t", "<", "|", ">"}
        char_ids = [v for k, v in vocab_dict.items() if k not in exclude]
        vocab_list = char_ids + ([newline_id] if newline_id is not None else []) + [eos_id]
    else:
        vocab_list = list(range(tokenizer.vocab_size - 1)) + [eos_id]

    prompt_text = _get_indice(template_id)
    input_ids = tokenizer(
        prompt_text, return_tensors="pt", add_special_tokens=True
    )["input_ids"]

    beam_width = list(cfg["beam_width"])
    search_width_cfg = cfg.get("search_width", None)
    if search_width_cfg is None:
        search_width = beam_width[:]
    elif isinstance(search_width_cfg, int):
        search_width = [search_width_cfg] * len(beam_width)
    else:
        search_width = list(search_width_cfg)

    batch_size = cfg.get("batch_size", 1000)
    eos_threshold = cfg.get("eos_threshold", 0.001)
    max_guess = cfg.get("max_guess_number", None)
    min_len = cfg.get("min_len", 0)

    print(
        f"[*] 搜索參數：beam_width[0]={beam_width[0]}, max_length={len(beam_width)}, "
        f"batch_size={batch_size}, eos_threshold={eos_threshold}"
    )

    start_time = time.time()
    results = dynamic_beam_search(
        model=model,
        input_ids=input_ids,
        batch_size=batch_size,
        beam_width_list=beam_width,
        vocab=vocab_list,
        eos_threshold=eos_threshold,
        search_width_list=search_width,
        min_len=min_len,
        seg_separator_id=newline_id,
    )
    elapsed = time.time() - start_time

    if max_guess:
        results = results[:max_guess]

    print(f"[*] 完成：找到 {len(results)} 個候選，耗時 {elapsed:.2f}s")

    output_dir = PROJECT_ROOT / cfg.get("output_path", "gen")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / cfg.get("output_file_name", "dynamic_beam_search_results.jsonl")

    with open(output_file, "w", encoding="utf-8") as f:
        for seq, prob in results:
            decoded = tokenizer.decode(seq.tolist(), skip_special_tokens=True)
            if len(decoded) < min_len:
                continue
            f.write(json.dumps({"password": decoded, "log_prob": prob.item()}, ensure_ascii=False) + "\n")

    print(f"[*] 結果已儲存至 {output_file}")


# ── Dispatcher ────────────────────────────────────────────────────────────────
# Maps search_type string → handler function.
# Duplicate keys handle common typos ("constrative" vs "contrastive").
_DISPATCHERS = {
    "contrastive_search": run_contrastive_search,
    "constrative_search": run_contrastive_search,
    "dynamic_beam_search": run_dynamic_beam_search,
}

_CANONICAL_NAMES = {
    "contrastive_search": "contrastive_search",
    "constrative_search": "contrastive_search",
    "dynamic_beam_search": "dynamic_beam_search",
}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Password search runner — reads config/search.yaml"
    )
    parser.add_argument(
        "--config", type=str,
        default=str(PROJECT_ROOT / "config" / "search.yaml"),
        help="Search config YAML path (default: config/search.yaml)",
    )
    cli_args = parser.parse_args()

    config = _load_yaml(cli_args.config)
    search_type = config.get("search_type", "contrastive_search")

    if search_type not in _DISPATCHERS:
        available = list(dict.fromkeys(_CANONICAL_NAMES.values()))
        print(f"[!] 未知的搜索方法：{search_type}")
        print(f"    可用方法：{available}")
        sys.exit(1)

    canonical = _CANONICAL_NAMES[search_type]
    print(f"[*] 使用搜索方法：{canonical}")

    # Look up the config section by both the original and canonical name
    search_cfg = config.get(search_type) or config.get(canonical) or {}
    _DISPATCHERS[search_type](search_cfg)
