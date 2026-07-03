from collections.abc import Collection, Iterable, Mapping
from difflib import SequenceMatcher


def normalize_search_text(text: str | None) -> str:
    """统一检索文本归一化；保留中文，压缩空白，英文小写。"""
    if not text:
        return ""
    return " ".join(str(text).lower().strip().split())


def build_search_document(parts: Iterable[str | None]) -> str:
    return normalize_search_text(" ".join(part for part in parts if part))


def text_similarity(left: str | None, right: str | None) -> float:
    normalized_left = normalize_search_text(left)
    normalized_right = normalize_search_text(right)
    if not normalized_left or not normalized_right:
        return 0
    if normalized_left == normalized_right:
        return 1
    if normalized_left in normalized_right or normalized_right in normalized_left:
        shorter = min(len(normalized_left), len(normalized_right))
        longer = max(len(normalized_left), len(normalized_right))
        return round(0.75 + 0.25 * (shorter / longer), 4)
    return round(SequenceMatcher(None, normalized_left, normalized_right).ratio(), 4)


def keyword_hit_score(text: str | None, keywords: Iterable[str]) -> float:
    normalized_text = normalize_search_text(text)
    normalized_keywords = {normalize_search_text(keyword) for keyword in keywords if keyword}
    if not normalized_text or not normalized_keywords:
        return 0
    hits = {keyword for keyword in normalized_keywords if keyword and keyword in normalized_text}
    return round(len(hits) / len(normalized_keywords), 4)


def overlap_score(left: Collection[str], right: Collection[str]) -> float:
    normalized_left = {normalize_search_text(item) for item in left if item}
    normalized_right = {normalize_search_text(item) for item in right if item}
    if not normalized_left or not normalized_right:
        return 0
    return round(len(normalized_left & normalized_right) / len(normalized_left | normalized_right), 4)


def weighted_score(components: Mapping[str, tuple[float, float]]) -> float:
    score = 0.0
    for value, weight in components.values():
        score += max(0.0, min(float(value), 1.0)) * float(weight)
    return round(score, 4)
