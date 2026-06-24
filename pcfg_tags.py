

dictionary={
  # ── Structural / backoff tags ──────────────────────────────────────────────
  "numberN": "A sequence of N digit characters (0-9). N is replaced by the actual length of the segment. Example: 'number3' represents a 3-digit number such as '123' or '456'.",
  "specialN": "A sequence of N non-alphanumeric special characters (e.g., '!', '@', '#'). N is replaced by the actual length. Example: 'special2' represents a 2-character symbol string such as '!!'.",
  "charN": "A sequence of N pure alphabetic characters that could not be assigned a part-of-speech tag, typically a random or meaningless character string. Example: 'char5' represents a 5-letter string such as 'aaaaa'.",
  "mixedN": "A segment of N characters containing a mixture of letters, digits, and/or special characters that does not fit into a single category. Example: 'mixed4' represents a segment such as 'a1!b'.",

  # ── Named-entity semantic tags ─────────────────────────────────────────────
  "mname": "A male given name.",
  "fname": "A female given name.",
  "city": "A city name.",
  "surname": "A family name or last name.",
  "country": "A country name.",

  # ── Nouns ──────────────────────────────────────────────────────────────────
  "nn": "A singular common noun.",
  "nn1": "A singular common noun.",
  "nn2": "A plural common noun.",
  "np": "A proper noun — a person, place, or named entity.",
  "np1": "A singular proper noun — a person's name, place, or named entity.",
  "np2": "A plural proper noun.",

  # ── Main verbs ─────────────────────────────────────────────────────────────
  "vv0": "A main verb in base/infinitive form.",
  "vvd": "A main verb in past tense form.",
  "vvg": "A main verb in present participle (-ing) form.",
  "vvn": "A main verb in past participle form.",
  "vvz": "A main verb in third-person singular present tense.",
  "vvi": "A main verb in infinitive form (after 'to').",
  "vvgk": "A main verb in -ing form used in a reduced clause.",

  # ── Adjectives / adverbs ───────────────────────────────────────────────────
  "jj": "A general adjective.",
  "jjr": "A comparative adjective.",
  "jjt": "A superlative adjective.",
  "rr": "A general adverb.",
  "rrr": "A comparative adverb.",
  "ra": "An unclassified adverb.",
  "rg": "A degree adverb ('very', 'quite', 'rather', 'too').",
  "rgr": "A comparative degree adverb ('more', 'less').",
  "rgt": "A superlative degree adverb ('most', 'least').",
  "rl": "A locative adverb ('here', 'there', 'away', 'home').",
  "rp": "An adverb functioning as a verb particle ('off', 'up', 'out', 'back').",
  "rrq": "A wh-adverb ('where', 'when', 'why', 'how').",
  "rrqv": "A wh-ever adverb ('wherever', 'whenever', 'however').",
  "rt": "A wh-adverb of time ('when', 'whenever').",
  "rrt": "A superlative adverb ('most', 'least', 'best').",
  "rgqv": "A wh-ever degree adverb ('however').",

  # ── Pronouns (closed class) ────────────────────────────────────────────────
  "ppis1": "The first-person singular subject pronoun 'I'.",
  "ppis2": "The first-person plural subject pronoun 'we'.",
  "ppy": "The second-person pronoun 'you'.",
  "pphs1": "The third-person singular subject pronoun 'he' or 'she'.",
  "pphs2": "The third-person plural subject pronoun 'they'.",
  "ppio1": "A first/third-person singular object pronoun ('me', 'him', 'her').",
  "ppio2": "A first/third-person plural object pronoun ('us', 'them').",
  "pph1": "The pronoun 'it'.",
  "ppho1": "A singular third-person object pronoun ('him', 'her', 'it').",
  "ppho2": "A plural third-person object pronoun ('them').",
  "ppx1": "A singular reflexive pronoun ('myself', 'himself', 'herself').",
  "ppx2": "A plural reflexive pronoun ('ourselves', 'themselves').",
  "ppx121": "A reflexive pronoun variant in a compound expression ('myself', 'yourself').",
  "ppge": "A possessive pronoun before a gerund ('my', 'his', 'their').",
  "appge": "A possessive pronoun used as pre-modifier ('my', 'your', 'his', 'her', 'our', 'their').",
  "pn": "An indefinite pronoun ('one', 'none', 'someone').",
  "pn1": "The indefinite pronoun 'one'.",
  "pnqs": "A wh-pronoun as subject in relative clauses ('who', 'whoever').",
  "pnqo": "A wh-pronoun used as object ('whom').",
  "pnqv": "A wh-pronoun in embedded questions ('who', 'what').",
  "pnx1": "A singular reflexive indefinite pronoun ('oneself').",
  "npx": "A negative indefinite pronoun ('nobody', 'nothing', 'no one').",

  # ── Articles (closed class) ────────────────────────────────────────────────
  "at": "The definite article 'the'.",
  "at1": "The indefinite article 'a' or 'an'.",

  # ── Prepositions / conjunctions ────────────────────────────────────────────
  "ii": "A general preposition ('in', 'on', 'at', 'of', 'for', 'with').",
  "io": "The preposition 'of'.",
  "ii31": "The first word of a multi-word preposition.",
  "ii21": "The first word of a two-word preposition.",
  "ii22": "The second word of a two-word preposition.",
  "if": "The preposition 'for'.",
  "iw": "The preposition 'with'.",
  "cc": "A coordinating conjunction ('and', 'or', 'but').",
  "ccb": "The coordinating conjunction 'but'.",
  "cs": "A subordinating conjunction ('that', 'if', 'because').",
  "csa": "The conjunction 'as'.",
  "csn": "The comparative conjunction 'than'.",
  "cst": "The subordinating conjunction 'that'.",
  "csw": "The subordinating conjunction 'while' or 'whilst'.",
  "to": "The infinitive marker 'to'.",

  # ── Determiners ────────────────────────────────────────────────────────────
  "da": "A post-determiner ('more', 'next', 'last').",
  "da1": "A singular after-determiner ('another', 'other').",
  "da2": "A plural after-determiner ('few', 'several', 'many').",
  "dar": "A comparative after-determiner ('more', 'less', 'fewer').",
  "dat": "A comparative determiner ('more', 'fewer', 'less').",
  "db": "A predeterminer ('all', 'both', 'half').",
  "db2": "A plural predeterminer ('all', 'both').",
  "dd": "A determiner or pronoun expressing quantity ('any', 'some', 'more').",
  "dd1": "A singular determiner expressing quantity ('much', 'little').",
  "dd2": "A plural determiner expressing quantity ('many', 'few').",
  "ddq": "A wh-determiner ('which', 'what').",
  "ddqv": "A wh-ever determiner ('whichever', 'whatever').",

  # ── Numbers ────────────────────────────────────────────────────────────────
  "mc": "A cardinal number.",
  "mc1": "The cardinal number 'one' or '1'.",
  "mc2": "A cardinal number used in plural context.",
  "md": "A decimal number or digit.",
  "mf": "A fraction or formula.",

  # ── Special nouns ──────────────────────────────────────────────────────────
  "nnu": "A unit of measurement ('km', 'kg', 'lb').",
  "nnu1": "A singular unit-of-measurement noun.",
  "nnu2": "A plural unit-of-measurement noun.",
  "nnb": "A broad or abstract singular noun.",
  "nna": "A noun of address ('sir', 'madam').",
  "nnt1": "A singular temporal noun ('day', 'month', 'year', 'morning').",
  "nnt2": "A plural temporal noun ('days', 'months', 'years').",
  "nnl1": "A singular locative noun ('home', 'here', 'abroad').",
  "nnl2": "A plural locative noun.",
  "nd1": "A singular ordinal noun ('next', 'last', 'first').",
  "nno": "A numeral noun ('dozen', 'score', 'hundred').",
  "npm1": "A month name.",
  "npm2": "A plural month name.",
  "npd1": "A day-of-week name.",
  "npd2": "A plural day-of-week name.",

  # ── Be-verb forms (closed class) ───────────────────────────────────────────
  "vb0": "The base form 'be'.",
  "vbi": "The infinitive 'be'.",
  "vbm": "'am' (first-person singular present of 'be').",
  "vbr": "'are' (second/plural present of 'be').",
  "vbz": "'is' (third-person singular present of 'be').",
  "vbd": "'was' or 'were' (past tense of 'be').",
  "vbdz": "'was' or 'were' (past tense of 'be').",
  "vbg": "'being' (present participle of 'be').",
  "vbn": "'been' (past participle of 'be').",
  "vbdr": "A contracted past form of 'be'.",

  # ── Do-verb forms (closed class) ───────────────────────────────────────────
  "vd0": "The base form 'do'.",
  "vdi": "The infinitive 'do'.",
  "vdz": "'does' (third-person singular present of 'do').",
  "vdd": "'did' (past tense of 'do').",
  "vdg": "'doing' (present participle of 'do').",
  "vdn": "'done' (past participle of 'do').",
  "vd": "A base or reduced form of 'do'.",

  # ── Have-verb forms (closed class) ────────────────────────────────────────
  "vh0": "The base form 'have'.",
  "vhi": "The infinitive 'have'.",
  "vhz": "'has' (third-person singular present of 'have').",
  "vhd": "'had' (past tense/participle of 'have').",
  "vhg": "'having' (present participle of 'have').",
  "vhn": "'had' (past participle of 'have').",

  # ── Other verbs / function words ───────────────────────────────────────────
  "vm": "A modal verb ('can', 'will', 'may', 'must', 'should', 'would').",
  "uh": "An interjection or exclamation.",
  "ex": "The existential 'there'.",
  "fw": "A foreign word.",
  "ge": "A genitive marker (possessive 's).",
  "xx": "The negative particle 'not'.",
  "zz1": "A single letter of the alphabet.",
  "zz2": "A sequence of repeated alphabet letters.",

  # ── Miscellaneous ──────────────────────────────────────────────────────────
  "j": "A short or unclassified adjective.",
  "jk": "An adjective in a compound expression.",
  "m": "A formula, symbol, or mathematical expression.",
  "m1": "A singular formula or measurement symbol.",
  "n": "A short or unclassified noun.",
  "c": "A short or unclassified conjunction.",
  "fo": "A foreign or formulaic word used as an object.",
  "fu": "An unclassified or foreign word.",
  "rex22": "The second part of a two-word expression containing a numeral or symbol.",

  "unk": "An alphabetic token with a valid part-of-speech but no matching entry in the semantic lexicon.",

  # ── Semantic / synset tags ─────────────────────────────────────────────────
  "<lemma>.<pos>.<id>": "A WordNet synset identifier used as a semantic tag in 'backoff' tagtype. Represents an abstract semantic class from the WordNet hierarchy, determined by a Tree Cut Model fitted on password frequencies. The synset granularity adapts to corpus evidence: frequent semantic categories are split finely, rare ones are merged into higher-level hypernym nodes. Example: 'love.v.01' denotes the synset for the verb 'love'; 'entity.n.01' denotes the root noun concept.",

  "<pos>_<synset>": "A combined tag encoding both syntactic role and semantic meaning. Example: 'vvd_love.v.01' means a past-tense verb belonging to the love synset.",
  "<pos>_unk": "A combined tag where the token has a valid part-of-speech but no matching semantic entry. Example: 'jj_unk' means an adjective with no semantic classification."
}


def tag_explain(dict_: dict=dictionary):
    return  dict_


import re

_STRUCTURAL_SHORT = {
    'number':  lambda n: f"{n}-digit number",
    'char':    lambda n: f"{n}-character alphabetic string",
    'special': lambda n: f"{n} special character{'s' if int(n) > 1 else ''}",
    'mixed':   lambda n: f"{n}-character mix of letters, digits, or symbols",
}

def expand_tag_description(tag: str, dict_: dict = dictionary) -> str:
    """Compact description for id=4: '<tag> — <short description>', no boilerplate."""
    m = re.fullmatch(r'(number|char|special|mixed)(\d+)', tag)
    if m:
        short = _STRUCTURAL_SHORT[m.group(1)](m.group(2))
        return f"{tag} — {short}"
    desc = get_explanation(tag, dict_)
    if desc == tag:
        return tag
    # Strip leading article and trailing period for a clean inline format
    desc = re.sub(r'^(A|An|The) ', '', desc).rstrip('.')
    desc = desc[0].lower() + desc[1:] if desc else desc
    return f"{tag} — {desc}"


_STRUCTURAL_EXPAND = {
    'number':  lambda n: f"A sequence of exactly {n} digit character{'s' if int(n) > 1 else ''} (0-9).",
    'char':    lambda n: f"A sequence of exactly {n} pure alphabetic character{'s' if int(n) > 1 else ''}.",
    'special': lambda n: f"Exactly {n} non-alphanumeric special character{'s' if int(n) > 1 else ''} (e.g., '!', '@', '#').",
    'mixed':   lambda n: f"A segment of exactly {n} character{'s' if int(n) > 1 else ''} mixing letters, digits, and/or special characters.",
}


def get_explanation(tag: str, dict_: dict = dictionary) -> str:
    """Look up the explanation for a tag, handling pattern-based keys."""
    if tag in dict_:
        return dict_[tag]
    # numberN / charN / specialN / mixedN — substitute actual N into description
    m = re.fullmatch(r'(number|char|special|mixed)(\d+)', tag)
    if m:
        return _STRUCTURAL_EXPAND[m.group(1)](m.group(2))
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
