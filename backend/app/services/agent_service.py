from backend.app.agents.analysis_graph import run_analysis_graph
from backend.app.schemas.analysis import AnalyzeRequest, AnalyzeResponse


class AnalysisUnavailableError(RuntimeError):
    """Raised when the analysis graph cannot produce executable SQL."""


class AgentService:
    """API 层的业务编排服务，负责调用 Agent 并返回前端契约。"""

    def analyze(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        question = payload.question.strip() or "最近 30 天销售额按天变化如何？"
        response = run_analysis_graph(question)
        if not response.sql and response.source.security != "未生成 SQL，等待用户确认":
            raise AnalysisUnavailableError("分析服务暂时无法生成可执行查询，请稍后重试。")
        return response
