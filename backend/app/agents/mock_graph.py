from backend.app.schemas.analysis import AnalyzeResponse
from backend.app.tools.mock_sql_tool import build_mock_analysis


def run_mock_agent_graph(question: str) -> AnalyzeResponse:
    """V1 mock graph：保留真实 LangGraph 之前的节点边界和返回结构。"""
    path = "rewrite_path" if "最近" in question else "cold_path"
    analysis = build_mock_analysis(question=question, path=path)
    return AnalyzeResponse(**analysis)
