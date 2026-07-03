def normalize_question(question: str) -> str:
    """标准化用户问题，供 SQL Memory 文本匹配使用。"""
    return " ".join(question.strip().lower().split())
