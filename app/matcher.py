"""Fuzzy matching utilities for comparing LLM output against ground truth."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

_TITLES = re.compile(
    r"\b(hon\.?|rep\.?|sen\.?|gov\.?|dr\.?|mr\.?|mrs\.?|ms\.?)\b",
    flags=re.IGNORECASE,
)
_NON_WORD = re.compile(r"[^\w\s\-]")
_WHITESPACE = re.compile(r"\s+")
_PROTOCOL = re.compile(r"^https?://")
_WWW = re.compile(r"^www\.")


def normalize_name(name: str) -> str:
    """Lowercase, strip honorific titles, collapse whitespace."""
    name = _TITLES.sub("", name)
    name = _NON_WORD.sub("", name)
    name = _WHITESPACE.sub(" ", name).strip().lower()
    return name


def normalize_url(url: str) -> str:
    """Strip protocol, www prefix, and trailing slash; lowercase."""
    url = url.strip().lower()
    url = _PROTOCOL.sub("", url)
    url = _WWW.sub("", url)
    return url.rstrip("/")


def names_match(expected: str, actual: str, threshold: float = 0.85) -> bool:
    """Return True if the two names are a fuzzy match after normalization.

    Checks in order:
    1. Exact match after normalization.
    2. Word-subset match (handles omitted middle names).
    3. SequenceMatcher ratio >= threshold.
    """
    norm_exp = normalize_name(expected)
    norm_act = normalize_name(actual)
    if norm_exp == norm_act:
        return True
    words_exp = set(norm_exp.split())
    words_act = set(norm_act.split())
    if words_exp.issubset(words_act) or words_act.issubset(words_exp):
        return True
    ratio = SequenceMatcher(None, norm_exp, norm_act).ratio()
    return ratio >= threshold


def urls_match(expected: str, actual: str) -> bool:
    """Return True if the two URLs are identical after normalization."""
    return normalize_url(expected) == normalize_url(actual)
