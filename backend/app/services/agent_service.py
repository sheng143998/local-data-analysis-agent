from backend.app.agents.analysis_graph import run_analysis_graph
from backend.app.schemas.analysis import AnalyzeRequest, AnalyzeResponse


class AgentService:
    """API 层的业务编排服务，负责调用 Agent 并返回前端契约。"""

    def analyze(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        question = payload.question.strip() or "最近 30 天销售额按天变化如何？"
        return run_analysis_graph(question)
