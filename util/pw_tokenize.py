import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pcfg_tags import get_explanation, expand_tag_description

def get_alpa(tokenizer):
    """提取 95 個可打印字符的 token 映射"""
    PW_WORD = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+,-./;<=>?@[\\]^_`{|}~ "
    vocab = {}
    for w in PW_WORD:
        vocab[w] = tokenizer(w)["input_ids"][-1]
    vocab[tokenizer.eos_token] = tokenizer.eos_token_id
    vocab["\t"] = tokenizer.eos_token_id  # \t 作為 EOS marker
    return vocab


def get_alpa_with_newline(tokenizer):
    """95-char vocab + newline as segment separator for template id=4."""
    vocab = get_alpa(tokenizer)
    vocab['\n'] = tokenizer('\n', add_special_tokens=False)['input_ids'][-1]
    return vocab

def encode_limit(input_str,vocab):
    new_str = input_str.replace("</s>", "\t")  # 處理 EOS token 在密碼中
    ret = [0 for i in range(len(new_str))]
    for i in range(len(new_str)):
        if new_str[i] == "\t":
            ret[i] = vocab["\t"]
        elif new_str[i] not in vocab.keys():
            ret[i] = 0  # <unk>
        else:
            ret[i] = vocab[new_str[i]]  
    return {
        "input_ids": ret,
        "attention_mask": [1 for i in range(len(ret))]
    }

def process_train_targeted(batch, prompt_ids, vocab, tokenizer, max_length=512, template_id=1):
    """Batched preprocessing: batch is a dict of lists (batched=True in dataset.map).
    prompt_ids must be pre-computed once outside the map call.
    template_id=1: token+tag pairs (training format A)
    template_id=2: structure-only, includes raw tag strings in structure/detail text
    template_id=3: structure-only with placeholders, no raw tag strings
    """
    passwords   = batch.get("Password", batch.get("passwords", []))
    tokens_col  = batch.get("Tokens", [])
    tags_col    = batch.get("Tags", [])

    prompt_len = len(prompt_ids)

    all_input_ids      = []
    all_attention_mask = []
    all_labels         = []

    for password, tokens, tags in zip(passwords, tokens_col, tags_col):
        password   = str(password) if password is not None else ""
        token_list = tokens.split("|") if tokens else []
        tag_list   = tags.split("|")   if tags   else []

        if template_id == 2:
            knowledge_text = json.dumps({
                "password structure": "(" + ")(".join(tag_list) + ")",
                "segment details": {
                    f"position {i + 1}": f"{get_explanation(tag)} ({tag})"
                    for i, tag in enumerate(tag_list)
                }
            }, ensure_ascii=False)
        elif template_id == 3:
            seg_keys = [f"<SEG{i + 1}>" for i in range(len(tag_list))]
            knowledge_text = json.dumps({
                "password structure": "(" + ")(".join(seg_keys) + ")" if seg_keys else "",
                "segment details": {
                    seg_key: get_explanation(tag)
                    for seg_key, tag in zip(seg_keys, tag_list)
                }
            }, ensure_ascii=False)
        elif template_id == 4:
            seg_keys = [f"<SEG{i + 1}>" for i in range(len(tag_list))]
            knowledge_text = json.dumps({
                "password structure": "(" + ")(".join(seg_keys) + ")" if seg_keys else "",
                "segment details": {
                    seg_key: expand_tag_description(tag)
                    for seg_key, tag in zip(seg_keys, tag_list)
                }
            }, ensure_ascii=False)
        elif template_id in ("3b", "4b"):
            # 3b: same user prompt as id=3 (get_explanation, no raw tag names)
            # 4b: same user prompt content (get_explanation, no raw tag names); different system text only
            seg_keys = [f"<SEG{i + 1}>" for i in range(len(tag_list))]
            knowledge_text = json.dumps({
                "password structure": "(" + ")(".join(seg_keys) + ")" if seg_keys else "",
                "segment details": {
                    seg_key: get_explanation(tag)
                    for seg_key, tag in zip(seg_keys, tag_list)
                }
            }, ensure_ascii=False)
        elif template_id == 5:
            # inline: <tag> placeholders only — training prompt matches inference prompt
            structure = ''.join(f"<{tag}>" for tag in tag_list)
            knowledge_text = json.dumps({"password structure": structure}, ensure_ascii=False)
        else:
            knowledge_text = json.dumps({
                "This password can be segmented and tag into the following part": list(zip(token_list, tag_list)),
                "For each segment, each tag represents the following meaning": {
                    tag: get_explanation(tag) for tag in set(tag_list)
                }
            }, ensure_ascii=False)
        knowledge_ids = tokenizer(knowledge_text, add_special_tokens=False)["input_ids"]

        # id=4 / 3b / 4b: encode each token segment separately with newline between segments
        if template_id in (4, "3b", "4b") and token_list:
            newline_id = vocab.get('\n', tokenizer('\n', add_special_tokens=False)['input_ids'][-1])
            password_ids = []
            for idx, token_str in enumerate(token_list):
                password_ids.extend(encode_limit(token_str, vocab)['input_ids'])
                if idx < len(token_list) - 1:
                    password_ids.append(newline_id)
        else:
            password_ids = encode_limit(password, vocab)["input_ids"]

        input_ids = prompt_ids + knowledge_ids + password_ids
        if tokenizer.eos_token_id is not None:
            input_ids = input_ids + [tokenizer.eos_token_id]

        input_ids      = input_ids[:max_length]
        attention_mask = [1] * len(input_ids)

        labels    = input_ids.copy()
        mask_upto = min(prompt_len + len(knowledge_ids), len(labels))
        labels[:mask_upto] = [-100] * mask_upto

        all_input_ids.append(input_ids)
        all_attention_mask.append(attention_mask)
        all_labels.append(labels)

    return {
        "input_ids":      all_input_ids,
        "attention_mask": all_attention_mask,
        "labels":         all_labels,
    }

