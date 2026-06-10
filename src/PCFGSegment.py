"""
PCFGSegment.py

Uses PCFG's own segmentation (regex + wordsegment) instead of BPE,
then tags each segment with the PCFG tagger.

Key difference from Tokenize.py:
  - BPE splits arbitrarily by frequency
  - PCFG splits by character class (alpha/digit/special) then uses
    wordsegment to find word boundaries within alphabetic runs

Segmentation example:
  dragon99!  →  ['dragon', '99', '!']   (PCFG-native)
  vs          →  ['drag', 'on', '99', '!']  (BPE, arbitrary)
"""

import sys
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class PCFGSegmenter:
    """
    Segment a password using PCFG's native approach, then tag each segment.

    Args:
        sg_path : absolute path to models/semantic-guesser/
        tagtype : 'pos' | 'backoff' | 'pos_semantic'
    """

    def __init__(self, sg_path: str, tagtype: str):
        sg_path = str(sg_path)
        if sg_path not in sys.path:
            sys.path.insert(0, sg_path)

        import wordsegment as ws
        ws.load()
        self._ws = ws

        from learning.pos import BackoffTagger
        from learning.model import GrammarTagger
        from learning.tagset_conversion import TagsetConverter
        from learning.train import pos_tag, POSBlacklist

        self._pos_tagger     = BackoffTagger()
        self._grammar_tagger = GrammarTagger()
        self._tag_converter  = TagsetConverter()
        self._blacklist      = POSBlacklist()
        self._pos_tag_fn     = pos_tag
        self.tagtype         = tagtype
        self._proper_noun_tags = set(BackoffTagger.proper_noun_tags())

        if tagtype in ('backoff', 'pos_semantic'):
            from nltk.corpus import wordnet as wn
            self._wordnet = wn
        else:
            self._wordnet = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _getchunks(self, password: str):
        """
        Split password into lowercased segments plus matching
        original-case slices.

        Returns:
            chunks_lower : list[str]  – segments used for POS tagging
            chunks_orig  : list[str]  – original-case segments for the CSV
        """
        pw_lower = password.lower()

        # 1. Coarse split: consecutive runs of letters / digits / specials
        temp = re.findall(r'([\W_]+|[a-zA-Z]+|[0-9]+)', pw_lower)

        chunks_lower = []
        for chunk in temp:
            if chunk[0].isalpha() and len(chunk) > 1:
                # 2. Fine split: use wordsegment to find word boundaries
                words = self._ws.segment(chunk)
                chunks_lower.extend(words)
            else:
                chunks_lower.append(chunk)

        if not chunks_lower:
            return [], []

        # 3. Map lowercased offsets back to original-case slices
        pos = 0
        chunks_orig = []
        for c in chunks_lower:
            length = len(c)
            chunks_orig.append(password[pos: pos + length])
            pos += length

        return chunks_lower, chunks_orig

    def _lookup_synset(self, word_lower: str, pos: str):
        """Return a synset name string, or None."""
        if self._wordnet is None:
            return None
        if pos is None or pos in self._proper_noun_tags:
            return None

        wn_pos = self._tag_converter.clawsToWordNet(pos)
        if wn_pos is None:
            return None

        min_length = 3 if wn_pos == 'n' else 2
        if len(word_lower) < min_length:
            return None

        synsets = self._wordnet.synsets(word_lower, wn_pos)
        return synsets[0].name() if synsets else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def segment_and_tag(self, password: str):
        """
        Segment a password and tag each segment.

        Returns:
            tokens : list[str]  – original-case segments
            tags   : list[str]  – PCFG tags
        """
        chunks_lower, chunks_orig = self._getchunks(password)
        if not chunks_lower:
            return [], []

        # pos_tag groups consecutive alpha chunks for context-aware POS tagging
        tagged = self._pos_tag_fn(chunks_lower, self._pos_tagger, self._blacklist)

        tokens = []
        tags   = []
        for i, (word_lower, pos) in enumerate(tagged):
            syn = self._lookup_synset(word_lower, pos)
            tag = self._grammar_tagger._get_tag(word_lower, pos, syn, self.tagtype)
            tokens.append(chunks_orig[i])
            tags.append(tag if tag else 'unk')

        return tokens, tags
