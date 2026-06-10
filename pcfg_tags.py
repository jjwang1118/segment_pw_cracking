

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
  "ppis2": "CLAWS7 part-of-speech tag for the first-person plural subject pronoun 'we'.",
  "ppy": "CLAWS7 part-of-speech tag for the second-person pronoun 'you'.",
  "pphs1": "CLAWS7 part-of-speech tag for the third-person singular subject pronoun 'he' or 'she'.",
  "ppio1": "CLAWS7 part-of-speech tag for the first/third-person singular object pronoun (me, him, her).",
  "ppio2": "CLAWS7 part-of-speech tag for the first/third-person plural object pronoun (us, them).",
  "pph1": "CLAWS7 part-of-speech tag for the pronoun 'it' (head position).",

  "at": "CLAWS7 part-of-speech tag for the definite article 'the'.",
  "at1": "CLAWS7 part-of-speech tag for the indefinite singular article 'a' or 'an'.",
  "ii": "CLAWS7 part-of-speech tag for a general preposition or subordinating conjunction (e.g., 'in', 'on', 'at', 'of').",
  "io": "CLAWS7 part-of-speech tag for the preposition 'of'.",
  "ii31": "CLAWS7 part-of-speech tag for the first word of a 3-word preposition.",
  "cc": "CLAWS7 part-of-speech tag for a coordinating conjunction (e.g., 'and', 'or', 'but').",
  "cs": "CLAWS7 part-of-speech tag for a subordinating conjunction (e.g., 'that', 'if', 'because').",
  "csa": "CLAWS7 part-of-speech tag for 'as' used as a comparative conjunction.",
  "to": "CLAWS7 part-of-speech tag for 'to' used as an infinitive marker.",
  "mc": "CLAWS7 part-of-speech tag for a cardinal number (e.g., '1', 'two', '100').",
  "md": "CLAWS7 part-of-speech tag for a decimal number or digit.",
  "mf": "CLAWS7 part-of-speech tag for a fraction or formula.",
  "nnu": "CLAWS7 part-of-speech tag for a singular noun representing a unit of measurement (e.g., 'km', 'kg', 'lb').",
  "nnb": "CLAWS7 part-of-speech tag for a broad or abstract singular noun.",
  "npm1": "CLAWS7 part-of-speech tag for a singular month name (e.g., 'January', 'March').",

  "vb0": "CLAWS7 part-of-speech tag for the base form of 'be'.",
  "vbi": "CLAWS7 part-of-speech tag for the infinitive form of 'be'.",
  "vbm": "CLAWS7 part-of-speech tag for 'am' (first-person singular present of 'be').",
  "vbr": "CLAWS7 part-of-speech tag for 'are' (second/plural present of 'be').",
  "vbz": "CLAWS7 part-of-speech tag for 'is' (third-person singular present of 'be').",
  "vbd": "CLAWS7 part-of-speech tag for 'was'/'were' (past tense of 'be').",
  "vbg": "CLAWS7 part-of-speech tag for 'being' (present participle of 'be').",
  "vbn": "CLAWS7 part-of-speech tag for 'been' (past participle of 'be').",
  "vd0": "CLAWS7 part-of-speech tag for the base form of 'do'.",
  "vdi": "CLAWS7 part-of-speech tag for the infinitive of 'do'.",
  "vdz": "CLAWS7 part-of-speech tag for 'does' (third-person singular present of 'do').",
  "vdd": "CLAWS7 part-of-speech tag for 'did' (past tense of 'do').",
  "vdg": "CLAWS7 part-of-speech tag for 'doing' (present participle of 'do').",
  "vdn": "CLAWS7 part-of-speech tag for 'done' (past participle of 'do').",
  "vh0": "CLAWS7 part-of-speech tag for the base form of 'have'.",
  "vhi": "CLAWS7 part-of-speech tag for the infinitive of 'have'.",
  "vhz": "CLAWS7 part-of-speech tag for 'has' (third-person singular present of 'have').",
  "vhd": "CLAWS7 part-of-speech tag for 'had' (past tense/participle of 'have').",
  "vhg": "CLAWS7 part-of-speech tag for 'having' (present participle of 'have').",
  "vhn": "CLAWS7 part-of-speech tag for 'had' (past participle of 'have').",
  "vm": "CLAWS7 part-of-speech tag for a modal auxiliary verb (e.g., 'can', 'will', 'may', 'should').",
  "vvi": "CLAWS7 part-of-speech tag for a main verb in the infinitive form (after 'to').",
  "uh": "CLAWS7 part-of-speech tag for an interjection or exclamation (e.g., 'oh', 'wow', 'hey').",
  "ex": "CLAWS7 part-of-speech tag for the existential 'there'.",
  "fw": "CLAWS7 part-of-speech tag for a foreign word.",
  "ge": "CLAWS7 part-of-speech tag for a genitive marker (possessive 's).",
  "zz1": "CLAWS7 part-of-speech tag for a singular letter of the alphabet.",
  "zz2": "CLAWS7 part-of-speech tag for a plural letter of the alphabet.",

  # Determiners / predeterminers
  "da": "CLAWS7 part-of-speech tag for a post-determiner or after-determiner (e.g., 'more', 'next', 'last').",
  "da2": "CLAWS7 part-of-speech tag for a plural after-determiner (e.g., 'few', 'several', 'many').",
  "dar": "CLAWS7 part-of-speech tag for a comparative after-determiner (e.g., 'more', 'less', 'fewer').",
  "db": "CLAWS7 part-of-speech tag for a predeterminer (e.g., 'all', 'both', 'half').",
  "dd": "CLAWS7 part-of-speech tag for a determiner/pronoun used to express quantity (e.g., 'any', 'some', 'more').",
  "dd1": "CLAWS7 part-of-speech tag for a singular determiner/pronoun indicating quantity (e.g., 'much', 'little').",
  "dd2": "CLAWS7 part-of-speech tag for a plural determiner/pronoun indicating quantity (e.g., 'many', 'few').",
  "ddq": "CLAWS7 part-of-speech tag for a wh-determiner (e.g., 'which', 'what').",
  "ddqv": "CLAWS7 part-of-speech tag for a wh-ever determiner (e.g., 'whichever', 'whatever').",
  "appge": "CLAWS7 part-of-speech tag for a possessive pronoun used as a pre-modifier (e.g., 'my', 'your', 'his', 'her', 'our', 'their').",

  # Pronouns
  "pn": "CLAWS7 part-of-speech tag for an indefinite pronoun (e.g., 'one', 'none', 'someone').",
  "pn1": "CLAWS7 part-of-speech tag for the indefinite pronoun 'one'.",
  "pnqs": "CLAWS7 part-of-speech tag for a wh-pronoun used as subject in relative clauses (e.g., 'who', 'whoever').",
  "ppge": "CLAWS7 part-of-speech tag for a possessive pronoun used before a gerund (e.g., 'my', 'his', 'their').",
  "ppho1": "CLAWS7 part-of-speech tag for a singular third-person object pronoun (e.g., 'him', 'her', 'it').",
  "ppho2": "CLAWS7 part-of-speech tag for a plural third-person object pronoun (e.g., 'them').",
  "ppx1": "CLAWS7 part-of-speech tag for a singular reflexive pronoun (e.g., 'myself', 'himself', 'herself').",
  "ppx2": "CLAWS7 part-of-speech tag for a plural reflexive pronoun (e.g., 'ourselves', 'themselves').",

  # Nouns – special classes
  "nna": "CLAWS7 part-of-speech tag for a noun of address (e.g., 'sir', 'madam', 'lord').",
  "nnt1": "CLAWS7 part-of-speech tag for a singular temporal noun (e.g., 'day', 'month', 'year', 'morning').",
  "nnt2": "CLAWS7 part-of-speech tag for a plural temporal noun (e.g., 'days', 'months', 'years').",
  "nnl1": "CLAWS7 part-of-speech tag for a singular locative noun (e.g., 'home', 'here', 'abroad').",
  "nnl2": "CLAWS7 part-of-speech tag for a plural locative noun.",
  "nnu1": "CLAWS7 part-of-speech tag for a singular noun representing a unit of measurement (variant spelling).",
  "nnu2": "CLAWS7 part-of-speech tag for a plural noun representing a unit of measurement.",
  "nd1": "CLAWS7 part-of-speech tag for a singular ordinal noun (e.g., 'next', 'last', 'first').",
  "npd1": "CLAWS7 part-of-speech tag for a singular day-of-week proper noun (e.g., 'Monday', 'Friday').",
  "npd2": "CLAWS7 part-of-speech tag for a plural day-of-week proper noun (e.g., 'Mondays').",
  "npx": "CLAWS7 part-of-speech tag for a negative indefinite pronoun (e.g., 'nobody', 'nothing', 'no one').",

  # Cardinals & numbers
  "mc1": "CLAWS7 part-of-speech tag for the singular cardinal number 'one' or '1'.",
  "mc2": "CLAWS7 part-of-speech tag for a cardinal number used in plural context.",

  # Adverbs
  "ra": "CLAWS7 part-of-speech tag for an unclassified adverb (e.g., 'again', 'also', 'still').",
  "rg": "CLAWS7 part-of-speech tag for a degree adverb (e.g., 'very', 'quite', 'rather', 'too').",
  "rgr": "CLAWS7 part-of-speech tag for a comparative degree adverb (e.g., 'more', 'less').",
  "rgt": "CLAWS7 part-of-speech tag for a superlative degree adverb (e.g., 'most', 'least').",
  "rl": "CLAWS7 part-of-speech tag for a locative adverb (e.g., 'here', 'there', 'away', 'home').",
  "rp": "CLAWS7 part-of-speech tag for an adverb functioning as a verb particle (e.g., 'off', 'up', 'out', 'back').",
  "rrq": "CLAWS7 part-of-speech tag for a wh-adverb (e.g., 'where', 'when', 'why', 'how').",
  "rrqv": "CLAWS7 part-of-speech tag for a wh-ever adverb (e.g., 'wherever', 'whenever', 'however').",
  "rt": "CLAWS7 part-of-speech tag for a wh-adverb of time (e.g., 'when', 'whenever').",

  # Conjunctions & prepositions
  "ccb": "CLAWS7 part-of-speech tag for the coordinating conjunction 'but'.",
  "csn": "CLAWS7 part-of-speech tag for the comparative conjunction 'than'.",
  "cst": "CLAWS7 part-of-speech tag for the subordinating conjunction 'that'.",
  "if": "CLAWS7 part-of-speech tag for the preposition 'for'.",
  "ii21": "CLAWS7 part-of-speech tag for the first word of a two-word preposition (e.g., 'out' in 'out of').",
  "ii22": "CLAWS7 part-of-speech tag for the second word of a two-word preposition (e.g., 'of' in 'out of').",
  "iw": "CLAWS7 part-of-speech tag for the preposition 'with'.",

  # Verbs – be forms
  "vbdz": "CLAWS7 part-of-speech tag for 'was'/'were' (past tense of 'be').",

  # Verbs – additional
  "vvgk": "CLAWS7 part-of-speech tag for the -ing form of a main verb in a reduced clause (e.g., 'knowing', 'doing').",
  "vbdr": "CLAWS7 part-of-speech tag for a reduced/contracted past form of 'be' (e.g., 'd in 'he'd').",
  "vd": "CLAWS7 part-of-speech tag for a base or reduced form of 'do'.",

  # Conjunctions – additional
  "csw": "CLAWS7 part-of-speech tag for the subordinating conjunction 'while' or 'whilst'.",

  # Pronouns – additional
  "pphs2": "CLAWS7 part-of-speech tag for the third-person plural subject pronoun 'they'.",
  "pnqo": "CLAWS7 part-of-speech tag for a wh-pronoun used as object (e.g., 'whom').",
  "pnqv": "CLAWS7 part-of-speech tag for a wh-pronoun used as subject in embedded questions (e.g., 'who', 'what').",
  "pnx1": "CLAWS7 part-of-speech tag for a singular reflexive indefinite pronoun (e.g., 'oneself').",

  # Determiners – additional
  "da1": "CLAWS7 part-of-speech tag for a singular after-determiner (e.g., 'another', 'other').",
  "db2": "CLAWS7 part-of-speech tag for a plural predeterminer (e.g., 'all', 'both').",
  "dat": "CLAWS7 part-of-speech tag for a comparative determiner (e.g., 'more', 'fewer', 'less').",

  # Adverbs – additional
  "rrt": "CLAWS7 part-of-speech tag for a superlative adverb (e.g., 'most', 'least', 'best').",
  "rgqv": "CLAWS7 part-of-speech tag for a wh-ever degree adverb (e.g., 'however').",

  # Nouns – additional
  "nno": "CLAWS7 part-of-speech tag for a numeral noun (e.g., 'dozen', 'score', 'hundred').",
  "npm2": "CLAWS7 part-of-speech tag for a plural month name (e.g., 'Januaries').",

  # Miscellaneous
  "j": "CLAWS7 part-of-speech tag for a short or unclassified adjective.",
  "jk": "CLAWS7 part-of-speech tag for an adjective occurring in a compound expression.",
  "m": "CLAWS7 part-of-speech tag for a formula, symbol, or mathematical expression.",
  "m1": "CLAWS7 part-of-speech tag for a singular formula or measurement symbol.",
  "n": "CLAWS7 part-of-speech tag for a short or unclassified noun.",
  "c": "CLAWS7 part-of-speech tag for a short or unclassified conjunction.",
  "fo": "CLAWS7 part-of-speech tag for a foreign or formulaic word used as an object.",
  "fu": "CLAWS7 part-of-speech tag for an unclassified or foreign word.",
  "rex22": "CLAWS7 part-of-speech tag for the second part of a two-word expression containing a numeral or symbol.",
  "ppx121": "CLAWS7 part-of-speech tag for a reflexive pronoun variant in a compound expression (e.g., 'myself', 'yourself').",
  "xx": "CLAWS7 part-of-speech tag for the negative particle 'not'.",

  "unk": "A tag assigned to an alphabetic token that has a valid part-of-speech tag but no matching synset in WordNet. Indicates a word outside the semantic lexicon.",

  "<lemma>.<pos>.<id>": "A WordNet synset identifier used as a semantic tag in 'backoff' tagtype. Represents an abstract semantic class from the WordNet hierarchy, determined by a Tree Cut Model fitted on password frequencies. The synset granularity adapts to corpus evidence: frequent semantic categories are split finely, rare ones are merged into higher-level hypernym nodes. Example: 'love.v.01' denotes the synset for the verb 'love'; 'entity.n.01' denotes the root noun concept.",

  "<pos>_<synset>": "A combined tag used in 'pos_semantic' tagtype, concatenating the CLAWS7 part-of-speech tag and the WordNet synset with an underscore. Encodes both syntactic role and semantic meaning simultaneously. Example: 'vvd_love.v.01' means a past-tense verb token belonging to the love synset.",
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
    # WordNet synset: lemma.pos.id  (with or without leading 's.')
    # Covers: love.v.01 / s.love.v.01 / red.s.01 / on-line.a.01 / ph.d..n.01
    if re.fullmatch(r'(?:s\.)?[a-z][a-z0-9._-]*[a-z0-9]\.[nvarsa]\.\d+|(?:s\.)?[a-z][a-z0-9._-]*\.[nvarsa]\.\d+', tag):
        return dict_.get('<lemma>.<pos>.<id>', tag)
    # <pos>_unk
    if tag.endswith('_unk'):
        return dict_.get('<pos>_unk', tag)
    # <pos>_<synset>: pos tag + underscore + synset (e.g. vvd_love.v.01)
    # Must contain a dot after the underscore to distinguish from plain CLAWS7 tags
    underscore_pos = tag.find('_')
    if underscore_pos > 0 and '.' in tag[underscore_pos:]:
        return dict_.get('<pos>_<synset>', tag)
    # CLAWS7 multi-word marker: base_tag + 2-3 digit suffix (e.g. ra21, rr22, nn121)
    # Strip the trailing digits and look up the base tag
    m = re.fullmatch(r'([a-z]+)\d{2,3}', tag)
    if m:
        base = m.group(1)
        if base in dict_:
            return dict_[base]
    return tag  # fallback: return the tag itself as-is
