import json
import re
from pcfg_tags import get_explanation, expand_tag_description

def _get_indice(id):
    if id == 0:
        return ("As a targeted password guessing model, your task is to utilize the provided account information to guess the password.")
    # train and inference give the model (token,tag) 
    if id == 1:
        return ("As a targeted password guessing model, your task is to generate likely password candidates based on the structural pattern and segment information provided.")
    # not give the model the actual token strings, only the tag sequence and per-tag descriptions, so it must infer the actual characters from its learned password distribution.
    if id == 2:
        return (
            "As a targeted password guessing model, your task is to generate likely password candidates "
            "that match the given structural pattern. Each segment describes only the character class and "
            "length — no actual characters are provided. Use your knowledge of common password patterns "
            "to fill in the most probable characters for each segment."
        )
    # structure-only with placeholder slots; no raw tag strings appear in prompt text
    if id == 3:
        return (
            "As a targeted password guessing model, your task is to generate likely password candidates "
            "that satisfy the segment constraints. The structure is represented with placeholder slots, "
            "and each slot includes only natural-language constraints. Do not output placeholders. "
            "Generate only plausible password characters that satisfy all slot constraints."
        )
    # placeholder slots with explicit length; output one segment per line
    if id == 4:
        return (
            "As a targeted password guessing model, your task is to generate likely password candidates "
            "that satisfy the segment constraints. Each slot specifies both the character class and the "
            "exact character count. Generate each segment on a separate line in the given order. "
            "Do not output placeholder names. Output only the characters satisfying each slot constraint."
        )
    # id=3 user prompt + per-segment newline output (no raw tag names)
    if id == "3b":
        return (
            "As a targeted password guessing model, your task is to generate likely password candidates "
            "that satisfy the segment constraints. The structure is represented with placeholder slots, "
            "and each slot includes only natural-language constraints. Do not output placeholders. "
            "Generate each segment on a separate line in the given order. "
            "Output only the characters satisfying each slot constraint."
        )
    # id=4 structure but descriptions use natural language (no raw tag names); per-segment output
    if id == "4b":
        return (
            "As a targeted password guessing model, your task is to generate likely password candidates "
            "that satisfy the segment constraints. The structure is represented with placeholder slots, "
            "and each slot includes natural-language descriptions of the character class and constraints. "
            "Generate each segment on a separate line in the given order. "
            "Do not output placeholder names. Output only the characters satisfying each slot constraint."
        )
    # inline: password structure is a sequence of <tag> placeholders, no descriptions
    if id == 5:
        return (
            "As a targeted password guessing model, your task is to generate likely password candidates "
            "that match the given tag structure. Each <tag> placeholder names the character class for "
            "that segment. Do not output the tag placeholders. "
            "Generate only the password characters for each segment in order."
        )
    raise ValueError(f"Unknown prompt id: {id}")


def prompt_convert(data: dict,template:str):
    tags=data['tag'].type(str).split('|') if data['tag'] is not None else []
    cut_list=data['cut_list'].split('|') # type:list
    password=data['password'].type(str) if data['password'] is not None else ''

    knowledge = json.dumps({
        "This password can be segmented and tag into the following part": list(zip(cut_list, tags))
    })

    explanation = json.dumps({
        "For each segment, each tag represents the following meaning": {
            tag: get_explanation(tag) for tag in set(tags)
        }
    })

    full_prompt= template+knowledge+explanation

    return full_prompt


def prompt_convert_structure_only(data: dict, template: str) -> str:
    """Template B (id=2): structure-only prompt, no actual token strings.

    The model receives only the tag sequence and per-tag descriptions, so it
    must infer the actual characters from its learned password distribution.

    Args:
        data: dict with keys 'Tags' (pipe-separated tag string) and optionally
              'Tokens' (not used here).
        template: system prompt string from _get_indice(2).

    Returns:
        Full prompt string to feed as model input.
    """
    tags = data['Tags'].split('|') if data.get('Tags') else []
    structure = '(' + ')('.join(tags) + ')'

    knowledge = json.dumps({
        "password structure": structure,
        "segment details": {
            f"position {i + 1}": f"{get_explanation(tag)} ({tag})"
            for i, tag in enumerate(tags)
        }
    }, ensure_ascii=False)

    return template + knowledge


def prompt_convert_structure_placeholder(data: dict, template: str) -> str:
    """Template C (id=3): structure-only with placeholders, no raw tag text.

    The model receives placeholder slots like [SEG1], [SEG2], ... and natural
    language constraints for each slot. This avoids exposing tag symbols such as
    "np1" in the prompt, reducing tag-string leakage into generated passwords.
    """
    tags = data['Tags'].split('|') if data.get('Tags') else []
    seg_keys = [f"<SEG{i + 1}>" for i in range(len(tags))]

    knowledge = json.dumps({
        "password structure": "(" + ")(".join(seg_keys) + ")" if seg_keys else "",
        "segment details": {
            seg_key: get_explanation(tag)
            for seg_key, tag in zip(seg_keys, tags)
        }
    }, ensure_ascii=False)

    return template + knowledge


def prompt_convert_token_tag(data: dict, template: str) -> str:
    """Template A (id=1): token+tag prompt — same format used during training.

    Includes the actual token strings as keys, so the model can directly
    read the segmented characters. Useful as a sanity check (near-trivial).

    Args:
        data: dict with keys 'Tokens' and 'Tags' (pipe-separated strings).
        template: system prompt string from _get_indice(1).

    Returns:
        Full prompt string to feed as model input.
    """
    tokens = data['Tokens'].split('|') if data.get('Tokens') else []
    tags   = data['Tags'].split('|')   if data.get('Tags')   else []

    knowledge = json.dumps({
        "This password can be segmented and tag into the following part": list(zip(tokens, tags)),
        "For each segment, each tag represents the following meaning": {
            tag: get_explanation(tag) for tag in set(tags)
        }
    }, ensure_ascii=False)

    return template + knowledge


def prompt_convert_segment_newline(data: dict, template: str) -> str:
    """Template D (id=4): C+B — one segment per line, N-expanded length descriptions.

    Combines:
      B: each segment description includes the exact character count (N substituted)
      C: training target is newline-separated segments, giving the model explicit
         segment boundaries in the output

    At inference the model generates newlines between segments; post-processing
    strips the newlines and concatenates to recover the full password.
    """
    tags = data['Tags'].split('|') if data.get('Tags') else []
    seg_keys = [f"<SEG{i + 1}>" for i in range(len(tags))]

    knowledge = json.dumps({
        "password structure": "(" + ")(".join(seg_keys) + ")" if seg_keys else "",
        "segment details": {
            seg_key: expand_tag_description(tag)
            for seg_key, tag in zip(seg_keys, tags)
        }
    }, ensure_ascii=False)

    return template + knowledge


def prompt_convert_structure_placeholder_newline(data: dict, template: str) -> str:
    """id=3b: same user prompt as id=3; training target uses per-segment newlines."""
    return prompt_convert_structure_placeholder(data, template)


def prompt_convert_no_tag_newline(data: dict, template: str) -> str:
    """id=4b: id=4 structure with natural-language descriptions (no raw tag names); per-segment output."""
    return prompt_convert_structure_placeholder(data, template)


def prompt_convert_inline(data: dict, template: str) -> str:
    """Template E (id=5): inline <tag> placeholders only, no segment text, no descriptions.

    Training and inference prompts are identical — only tag names appear in the
    password structure. The model must infer segment content from the tag name alone.
    Example: {"password structure": "<mname><char1><number5>"}
    """
    tags = data['Tags'].split('|') if data.get('Tags') else []
    structure = ''.join(f"<{tag}>" for tag in tags)
    knowledge = json.dumps({"password structure": structure}, ensure_ascii=False)
    return template + knowledge


def get_prompt_template(id: int) -> str:
    """Return the system prompt string for a given template id."""
    return _get_indice(id)




