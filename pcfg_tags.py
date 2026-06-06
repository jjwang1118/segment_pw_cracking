

dictionary={
  "numberN": "A sequence of N digit characters (0-9). N is replaced by the actual length of the segment. Example: 'number3' represents a 3-digit number such as '123' or '456'.",
  "specialN": "A sequence of N non-alphanumeric special characters (e.g., '!', '@', '#'). N is replaced by the actual length. Example: 'special2' represents a 2-character symbol string such as '!!'.",
  "charN": "A sequence of N pure alphabetic characters that could not be assigned a part-of-speech tag, typically a random or meaningless character string. Example: 'char5' represents a 5-letter string such as 'aaaaa'.",
  "mixedN": "A segment of N characters containing a mixture of letters, digits, and/or special characters that does not fit into a single category. Example: 'mixed4' represents a segment such as 'a1!b'.",

  "mname": "A token recognized as a male given name based on a curated name list (e.g., 'Jacob', 'Michael'). Used as a proper noun semantic tag.",
  "fname": "A token recognized as a female given name based on a curated name list (e.g., 'Emily', 'Jessica'). Used as a proper noun semantic tag.",
  "city": "A token recognized as a city name based on a curated geographic list (e.g., 'paris', 'london'). Used as a proper noun semantic tag.",
  "surname": "A token recognized as a family name or last name based on a curated surname list (e.g., 'smith', 'johnson'). Used as a proper noun semantic tag.",
  "country": "A token recognized as a country name based on a curated geographic list (e.g., 'france', 'china'). Used as a proper noun semantic tag.",

  "nn": "CLAWS7 part-of-speech tag for a singular common noun (e.g., 'food', 'love', 'house'). Derived from WordNet noun synsets.",
  "nn1": "CLAWS7 part-of-speech tag for a singular common noun, equivalent to 'nn'. Assigned by corpus-trained taggers (e.g., 'book', 'dog').",
  "nn2": "CLAWS7 part-of-speech tag for a plural common noun (e.g., 'houses', 'books', 'dogs').",
  "np": "CLAWS7 part-of-speech tag for a proper noun, typically a named entity (e.g., 'Jacob', 'London').",
  "np1": "CLAWS7 part-of-speech tag for a singular proper noun (e.g., 'Paris', 'John'). Assigned by the COCA or corpus-trained tagger.",
  "np2": "CLAWS7 part-of-speech tag for a plural proper noun (e.g., 'Americans', 'Romans').",
  "vv0": "CLAWS7 part-of-speech tag for the base form of a main verb (infinitive). Example: 'give', 'run', 'love'.",
  "vvd": "CLAWS7 part-of-speech tag for the past tense form of a main verb. Example: 'gave', 'loved', 'ran'.",
  "vvg": "CLAWS7 part-of-speech tag for the present participle (-ing form) of a main verb. Example: 'giving', 'loving', 'running'.",
  "vvn": "CLAWS7 part-of-speech tag for the past participle form of a main verb. Example: 'given', 'loved', 'run'.",
  "vvz": "CLAWS7 part-of-speech tag for the third-person singular present tense of a main verb. Example: 'gives', 'loves', 'runs'.",
  "jj": "CLAWS7 part-of-speech tag for a general adjective. Example: 'great', 'hot', 'beautiful'.",
  "jjr": "CLAWS7 part-of-speech tag for a comparative adjective. Example: 'greater', 'hotter', 'more beautiful'.",
  "jjt": "CLAWS7 part-of-speech tag for a superlative adjective. Example: 'greatest', 'hottest'.",
  "rr": "CLAWS7 part-of-speech tag for a general adverb. Example: 'quickly', 'always', 'never'.",
  "rrr": "CLAWS7 part-of-speech tag for a comparative adverb. Example: 'faster', 'more quickly'.",
  "ppis1": "CLAWS7 part-of-speech tag for the first-person singular subject pronoun 'I'.",
  "ppy": "CLAWS7 part-of-speech tag for the second-person pronoun 'you'.",
  "unk": "A tag assigned to an alphabetic token that has a valid part-of-speech tag but no matching synset in WordNet. Indicates a word outside the semantic lexicon.",

  "s.<lemma>.<pos>.<id>": "A WordNet synset identifier used as a semantic tag in 'backoff' tagtype. Represents an abstract semantic class from the WordNet hierarchy, determined by a Tree Cut Model fitted on password frequencies. The synset granularity adapts to corpus evidence: frequent semantic categories are split finely, rare ones are merged into higher-level hypernym nodes. Example: 's.love.v.01' denotes the synset for the verb 'love'; 's.entity.n.01' denotes the root noun concept.",

  "<pos>_<synset>": "A combined tag used in 'pos_semantic' tagtype, concatenating the CLAWS7 part-of-speech tag and the WordNet synset with an underscore. Encodes both syntactic role and semantic meaning simultaneously. Example: 'vvd_s.love.v.01' means a past-tense verb token belonging to the love synset.",
  "<pos>_unk": "A combined tag used in 'pos_semantic' tagtype when a token has a valid part-of-speech but no matching WordNet synset. The suffix '_unk' indicates semantic unknownness. Example: 'jj_unk' means an adjective with no WordNet entry."
}


def tag_explain(dict_: dict=dictionary):
    return  dict_


import re

def get_explanation(tag: str, dict_: dict = dictionary) -> str:
    """Look up the explanation for a tag, handling pattern-based keys."""
    if tag in dict_:
        return dict_[tag]
    # numberN / charN / specialN / mixedN
    for prefix in ('number', 'char', 'special', 'mixed'):
        if re.fullmatch(prefix + r'\d+', tag):
            return dict_.get(prefix + 'N', tag)
    # s.<lemma>.<pos>.<id>  (WordNet synset)
    if re.fullmatch(r's\.[a-z_]+\.[nvar]\.\d+', tag):
        return dict_.get('s.<lemma>.<pos>.<id>', tag)
    # <pos>_unk
    if tag.endswith('_unk'):
        return dict_.get('<pos>_unk', tag)
    # <pos>_<synset>
    if '_s.' in tag:
        return dict_.get('<pos>_<synset>', tag)
    return tag  # fallback: return the tag itself as-is