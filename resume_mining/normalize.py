from __future__ import annotations

from typing import List

import re
from parsivar import Normalizer as ParsivarNormalizer, Tokenizer as ParsivarTokenizer


_normalizer = ParsivarNormalizer()
_tokenizer = ParsivarTokenizer()


def normalize_persian(text: str) -> str:
    """Normalize Persian text (diacritics, punctuation, Arabic/Persian forms)."""
    text = _normalizer.normalize(text or "")
    # unify digits to Persian and strip zero-width joiners
    text = text.replace("\u200c", " ")
    # remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize_words(text: str) -> List[str]:
    # Parsivar tokenizer returns a list of tokens
    return _tokenizer.tokenize_words(text or "")
