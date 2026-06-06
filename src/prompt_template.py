import json
from pcfg_tags import get_explanation

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


def get_prompt_template(id: int) -> str:
    """Return the system prompt string for a given template id."""
    return _get_indice(id)




