"""
run_eval.py — targeted password guessing evaluation entry point.

For each test entry in test_data.jsonl:
  1. Build knowledge prompt from Tokens + Tags (real password never shown to model)
  2. Run contrastive_search to generate candidate passwords
  3. Check if real password appears in candidates → min_cracked_guess_number
  4. Write per-entry JSONL and print aggregate crack-rate stats

Usage:
    python run_eval.py
    python run_eval.py --config config/search.yaml
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import sys
import json
import time
import yaml
import torch
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def _load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_model_path(eval_cfg: dict, search_cfg: dict) -> str:
    """Return model path: eval_cfg > search_cfg > train_config.yaml fallback."""
    for cfg in (eval_cfg, search_cfg):
        if "model_path" in cfg:
            return str(PROJECT_ROOT / cfg["model_path"])
    train_cfg = _load_yaml(PROJECT_ROOT / "config" / "train_config.yaml")
    tc = train_cfg["train"]["train_config"]
    return str(PROJECT_ROOT / tc["model_path"] / tc["model_name"])


def _load_model(model_path: str, precision: str):
    """Load model. Automatically detects LoRA adapter and loads with PEFT if present."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype  = {"half": torch.float16, "bf16": torch.bfloat16}.get(precision, torch.float32) \
             if device == "cuda" else torch.float32

    is_lora = (Path(model_path) / "adapter_config.json").exists()

    if is_lora:
        # LoRA checkpoint: load base model first, then adapter
        import json as _json
        adapter_cfg = _json.loads((Path(model_path) / "adapter_config.json").read_text())
        base_path   = adapter_cfg.get("base_model_name_or_path", "")
        # Prefer local base model if path exists, otherwise use adapter_cfg value
        local_base  = PROJECT_ROOT / "models" / Path(base_path).name
        base_path   = str(local_base) if local_base.exists() else base_path
        print(f"[*] 載入基底模型：{base_path}  (device={device}, dtype={dtype})")
        tokenizer = AutoTokenizer.from_pretrained(base_path)
        model     = AutoModelForCausalLM.from_pretrained(base_path, torch_dtype=dtype)
        from peft import PeftModel
        print(f"[*] 載入 LoRA adapter：{model_path}")
        model = PeftModel.from_pretrained(model, model_path)
        model = model.merge_and_unload()   # merge for faster inference
    else:
        print(f"[*] 載入模型：{model_path}  (device={device}, dtype={dtype})")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model     = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=dtype)

    model.to(device)
    model.eval()
    return model, tokenizer, device


def _build_prompt(entry: dict, template_id: int, system_prompt: str) -> str:
    """Build the full prompt string for one test entry (no real password included)."""
    if template_id == 1:
        from src.prompt_template import prompt_convert_token_tag
        return prompt_convert_token_tag(entry, system_prompt)
    if template_id == 2:
        from src.prompt_template import prompt_convert_structure_only
        return prompt_convert_structure_only(entry, system_prompt)
    if template_id == 3:
        from src.prompt_template import prompt_convert_structure_placeholder
        return prompt_convert_structure_placeholder(entry, system_prompt)
    if template_id == 4:
        from src.prompt_template import prompt_convert_segment_newline
        return prompt_convert_segment_newline(entry, system_prompt)
    if template_id in ("3b", "4b"):
        from src.prompt_template import prompt_convert_structure_placeholder
        return prompt_convert_structure_placeholder(entry, system_prompt)
    if template_id == 5:
        from src.prompt_template import prompt_convert_inline
        return prompt_convert_inline({"Tags": entry.get("Tags")}, system_prompt)
    if template_id == 6:
        from src.prompt_template import prompt_convert_inline_plain
        return prompt_convert_inline_plain({"Tags": entry.get("Tags")}, system_prompt)
    if template_id == 7:
        from src.prompt_template import prompt_convert_sibling_tag
        return prompt_convert_sibling_tag(
            {"Tags": entry.get("Tags"), "Siblings": entry.get("Siblings")}, system_prompt
        )
    if template_id == 8:
        from src.prompt_template import prompt_convert_multi_structure
        return prompt_convert_multi_structure(
            {"Tags": entry.get("Tags"), "CandTags": entry.get("CandTags")}, system_prompt
        )
    raise ValueError(f"Unknown template_id: {template_id}")


def run_eval(search_cfg: dict, eval_cfg: dict, search_type: str = "contrastive_search"):
    from util.search import contrastive_search, dynamic_beam_search, \
        dynamic_beam_search_Constrained_Decoding, build_step_constraints, \
        contrastive_search_Constrained_Decoding
    from util.pw_tokenize import get_alpa
    from src.prompt_template import _get_indice

    # ── Model ─────────────────────────────────────────────────────────────────
    model_path = _resolve_model_path(eval_cfg, search_cfg)
    precision  = search_cfg.get("precistion", "full")
    model, tokenizer, device = _load_model(model_path, precision)

    # ── Search params ─────────────────────────────────────────────────────────
    template_id  = search_cfg.get("prompt_template_id", 1)

    # ── Vocab ─────────────────────────────────────────────────────────────────
    from util.pw_tokenize import get_alpa_with_newline
    _use_newline = template_id in (4, "3b", "4b")
    vocab_dict = get_alpa_with_newline(tokenizer) if _use_newline else get_alpa(tokenizer)

    # SentencePiece space-strip detection: use two-char combined decode.
    # Single-char decode([▁d]) returns "d" (no space), so single-token probe
    # gives a false negative. Two-char decode([▁d,▁r]) returns "d r" for SPM
    # and "dr" for tiktoken — this reliably distinguishes the two families.
    _pd, _pr = vocab_dict.get('d'), vocab_dict.get('r')
    _needs_space_strip = bool(
        _pd is not None and _pr is not None
        and tokenizer.decode([_pd, _pr]) != "dr"
    )
    eos_id     = tokenizer.eos_token_id
    newline_id = tokenizer('\n', add_special_tokens=False)['input_ids'][-1] if _use_newline else None
    if search_cfg.get("vocab_limit", True):
        exclude = {tokenizer.eos_token, "\t", "<", "|", ">"}
        char_ids = [v for k, v in vocab_dict.items() if k not in exclude]
        # id=4: include newline before EOS so the model can emit segment separators
        vocab_list = char_ids + ([newline_id] if newline_id is not None else []) + [eos_id]
    else:
        vocab_list = list(range(tokenizer.vocab_size - 1)) + [eos_id]

    # Constrained search uses vocab_dict directly (builds per-step masks internally).
    # Same exclusion set as vocab_list to avoid <|...|> artifacts.
    _EXCLUDE = {tokenizer.eos_token, "\t", "<", "|", ">"}
    constrained_vocab_dict = {c: tid for c, tid in vocab_dict.items() if c not in _EXCLUDE}

    system_prompt = _get_indice(template_id)

    # Params shared by contrastive / dynamic beam search
    beam_width_list  = list(search_cfg["beam_width"]) if isinstance(search_cfg.get("beam_width"), list) \
                       else [search_cfg.get("beam_width", 95)] * 16
    search_width_cfg = search_cfg.get("search_width", None)
    if search_width_cfg is None:
        search_width = beam_width_list[:]
    elif isinstance(search_width_cfg, int):
        search_width = [search_width_cfg] * len(beam_width_list)
    else:
        search_width = list(search_width_cfg)

    batch_size    = search_cfg.get("batch_size", 1000)
    eos_threshold = search_cfg.get("eos_threshold", 0.001)
    max_guess     = search_cfg.get("max_guess_number", 1000)
    min_len       = search_cfg.get("min_len", 0)
    alpha         = search_cfg.get("contrastive_alpha", 0.6)
    use_contrast  = search_cfg.get("use_contrastive", True)

    # Params for constrained beam search / constrained contrastive search (single int, not list)
    c_beam_width   = search_cfg.get("beam_width", 1000) if not isinstance(search_cfg.get("beam_width"), list) \
                     else search_cfg["beam_width"][1]
    c_search_width = search_cfg.get("search_width", c_beam_width)
    c_fallback     = search_cfg.get("fallback_to_dynamic", True)
    c_alpha        = search_cfg.get("contrastive_alpha", 0.6)
    c_use_contrast = search_cfg.get("use_contrastive", True)

    # ── Eval params ───────────────────────────────────────────────────────────
    test_data_path   = PROJECT_ROOT / eval_cfg["test_data_path"]
    max_eval_samples = eval_cfg.get("max_eval_samples", None)
    output_dir       = PROJECT_ROOT / search_cfg.get("output_path", "gen")
    output_file      = output_dir / eval_cfg.get("eval_output_file_name", "eval_results.jsonl")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load test data ────────────────────────────────────────────────────────
    with open(test_data_path, "r", encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]
    if max_eval_samples:
        entries = entries[:max_eval_samples]
    total = len(entries)
    print(f"[*] 評估筆數：{total}  |  template_id={template_id}  |  max_guess={max_guess}")
    print(f"[*] 輸出路徑：{output_file}\n")

    # ── Eval loop ─────────────────────────────────────────────────────────────
    all_results = []
    import traceback as _tb
    with open(output_file, "w", encoding="utf-8") as out_f:
        for i, entry in enumerate(entries):
            real_pw     = str(entry.get("Password", ""))
            full_prompt = _build_prompt(entry, template_id, system_prompt)

            input_ids = tokenizer(
                full_prompt, return_tensors="pt", add_special_tokens=True
            )["input_ids"].to(device)

            t0 = time.time()
            try:
                if search_type == "constrained_contrastive_search":
                    tags_str = entry.get("Tags", "")
                    step_ids, _ = build_step_constraints(tags_str, constrained_vocab_dict, eos_id)
                    if step_ids is not None:
                        raw_results = contrastive_search_Constrained_Decoding(
                            model=model,
                            input_ids=input_ids,
                            tags_str=tags_str,
                            vocab_dict=constrained_vocab_dict,
                            eos_id=eos_id,
                            batch_size=batch_size,
                            beam_width=c_beam_width,
                            search_width=c_search_width,
                            use_contrastive=c_use_contrast,
                            contrastive_alpha=c_alpha,
                        )
                    elif c_fallback:
                        print(f"  [fallback→contrastive] tags='{tags_str}' 含 pos/semantic tag", flush=True)
                        raw_results = contrastive_search(
                            model=model,
                            input_ids=input_ids,
                            batch_size=batch_size,
                            beam_width_list=list(beam_width_list),
                            vocab=vocab_list,
                            eos_threshold=eos_threshold,
                            search_width_list=list(search_width),
                            use_contrastive=use_contrast,
                            contrastive_alpha=alpha,
                            min_len=min_len,
                            seg_separator_id=newline_id,
                        )
                    else:
                        raw_results = []
                elif search_type == "constrained_beam_search":
                    tags_str = entry.get("Tags", "")
                    step_ids, _ = build_step_constraints(tags_str, constrained_vocab_dict, eos_id)
                    if step_ids is not None:
                        raw_results = dynamic_beam_search_Constrained_Decoding(
                            model=model,
                            input_ids=input_ids,
                            tags_str=tags_str,
                            vocab_dict=constrained_vocab_dict,
                            eos_id=eos_id,
                            batch_size=batch_size,
                            beam_width=c_beam_width,
                            search_width=c_search_width,
                        )
                    elif c_fallback:
                        print(f"  [fallback→dynamic] tags='{tags_str}' 含 pos/semantic tag", flush=True)
                        raw_results = dynamic_beam_search(
                            model=model,
                            input_ids=input_ids,
                            batch_size=batch_size,
                            beam_width_list=list(beam_width_list),
                            vocab=vocab_list,
                            eos_threshold=eos_threshold,
                            search_width_list=list(search_width),
                            min_len=min_len,
                            seg_separator_id=newline_id,
                        )
                    else:
                        raw_results = []
                elif search_type == "dynamic_beam_search":
                    raw_results = dynamic_beam_search(
                        model=model,
                        input_ids=input_ids,
                        batch_size=batch_size,
                        beam_width_list=list(beam_width_list),
                        vocab=vocab_list,
                        eos_threshold=eos_threshold,
                        search_width_list=list(search_width),
                        min_len=min_len,
                        seg_separator_id=newline_id,
                    )
                else:
                    raw_results = contrastive_search(
                        model=model,
                        input_ids=input_ids,
                        batch_size=batch_size,
                        beam_width_list=list(beam_width_list),
                        vocab=vocab_list,
                        eos_threshold=eos_threshold,
                        search_width_list=list(search_width),
                        use_contrastive=use_contrast,
                        contrastive_alpha=alpha,
                        min_len=min_len,
                        seg_separator_id=newline_id,
                    )
            except Exception as exc:
                err_msg = _tb.format_exc()
                print(f"\n[!] 樣本 {i} (pw={real_pw!r}) 搜尋失敗：\n{err_msg}", flush=True)
                result = {
                    "index": i, "real_password": real_pw,
                    "tokens": entry.get("Tokens", ""), "tags": entry.get("Tags", ""),
                    "source": entry.get("source", ""), "model_input": full_prompt,
                    "candidates": [], "min_cracked_guess_number": 0,
                    "error": str(exc),
                }
                out_f.write(json.dumps(result, ensure_ascii=False) + "\n")
                all_results.append(result)
                torch.cuda.empty_cache()
                continue

            elapsed = time.time() - t0

            # Decode and filter candidates
            candidates = []
            for seq, prob in raw_results:
                decoded = tokenizer.decode(seq.tolist(), skip_special_tokens=True)
                if _needs_space_strip:
                    decoded = decoded.replace(" ", "")
                if len(decoded) >= min_len:
                    candidates.append([decoded, prob.item()])
                if len(candidates) >= max_guess:
                    break

            decoded_pws = [pw for pw, _ in candidates]
            rank = decoded_pws.index(real_pw) + 1 if real_pw in decoded_pws else 0

            result = {
                "index":                    i,
                "real_password":            real_pw,
                "tokens":                   entry.get("Tokens", ""),
                "tags":                     entry.get("Tags",   ""),
                "source":                   entry.get("source", ""),
                "model_input":              full_prompt,
                "candidates":               candidates,
                "min_cracked_guess_number": rank,
            }
            out_f.write(json.dumps(result, ensure_ascii=False) + "\n")
            all_results.append(result)

            cracked_so_far = sum(1 for r in all_results if r["min_cracked_guess_number"] > 0)
            print(
                f"[{i+1:>4}/{total}] pw={real_pw!r:20s}  rank={rank:>5}  "
                f"cands={len(candidates):>4}  t={elapsed:.1f}s  "
                f"cracked={cracked_so_far}/{i+1}"
            )
            # clean gpu memory after each entry to avoid OOM
            torch.cuda.empty_cache()
    # ── Aggregate crack-rate stats ────────────────────────────────────────────
    print("\n── Crack Rate ──────────────────────────────────────────────")
    for k in [1, 10, 100, 1000]:
        cracked = sum(1 for r in all_results if 0 < r["min_cracked_guess_number"] <= k)
        print(f"  @{k:<5}: {cracked:>4} / {total}  ({cracked / total:.2%})")
    print(f"\n[*] 結果已儲存至 {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluation runner — reads config/search.yaml")
    parser.add_argument(
        "--config", type=str,
        default=str(PROJECT_ROOT / "config" / "search.yaml"),
        help="Search config YAML path (default: config/search.yaml)",
    )
    cli_args = parser.parse_args()

    config      = _load_yaml(cli_args.config)
    search_type = config.get("search_type", "contrastive_search")
    _CANONICAL = {
        "constrative_search":               "contrastive_search",
        "contrastive_search":               "contrastive_search",
        "dynamic_beam_search":              "dynamic_beam_search",
        "constrained_beam_search":          "constrained_beam_search",
        "constrained_contrastive_search":   "constrained_contrastive_search",
    }
    canonical   = _CANONICAL.get(search_type, "contrastive_search")
    search_cfg  = config.get(search_type) or config.get(canonical) or {}
    eval_cfg    = config.get("eval", {})

    run_eval(search_cfg, eval_cfg, search_type=canonical)
