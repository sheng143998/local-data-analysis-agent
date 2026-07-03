from backend.app.tools.retrieval_scoring import (
    build_search_document,
    keyword_hit_score,
    normalize_search_text,
    overlap_score,
    text_similarity,
    weighted_score,
)


def test_normalize_search_text_keeps_chinese_and_lowercases_english() -> None:
    assert normalize_search_text("  GMV   销售额  ") == "gmv 销售额"


def test_build_search_document_skips_empty_parts() -> None:
    assert build_search_document(["orders", None, "", "total_amount"]) == "orders total_amount"


def test_text_similarity_handles_exact_and_containment_matches() -> None:
    assert text_similarity("最近30天销售额", "最近30天销售额") == 1
    assert text_similarity("销售额", "最近30天销售额按天变化") > 0.75


def test_keyword_hit_score_counts_unique_hits() -> None:
    score = keyword_hit_score("最近 30 天销售额和订单数", {"销售额", "订单数", "退款率"})

    assert score == 0.6667


def test_overlap_score_uses_normalized_jaccard() -> None:
    assert overlap_score({"Orders", "payments"}, {"orders", "refunds"}) == 0.3333


def test_weighted_score_clamps_component_values() -> None:
    score = weighted_score({"a": (2, 0.6), "b": (0.5, 0.4)})

    assert score == 0.8
