from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException

from backend.app.agents.analysis_graph import run_analysis_graph
from backend.app.core.config import settings
from backend.app.schemas.analysis import AnalyzeRequest, AnalyzeResponse, ConversationDetail, ConversationMessage, ConversationSummary
from backend.app.schemas.conversation import ConversationState, CurrentAnalysis
from backend.app.services.conversation_store import ConversationStore, get_conversation_store
from backend.app.services.followup_resolver import pending_from_intent, resolve_followup
from backend.app.services.long_term_memory_service import LongTermMemoryService
from backend.app.services.working_memory import build_working_context, refresh_working_memory
from backend.app.tools.analysis_presenter import present_clarification_response
from backend.app.tools.question_intent_parser import ParsedQuestionIntent, parse_question_intent
from backend.app.tools.semantic_resolver import apply_semantic_resolution
from backend.app.tools.clarification_policy import apply_clarification_policy


class AnalysisUnavailableError(RuntimeError):
    """Raised when the analysis graph cannot produce executable SQL."""


class AgentService:
    """API 层的业务编排服务，负责调用 Agent 并返回前端契约。"""

    def __init__(self, conversation_store: ConversationStore | None = None, long_term_memory_service: LongTermMemoryService | None = None) -> None:
        self.conversation_store = conversation_store or get_conversation_store()
        self.long_term_memory_service = long_term_memory_service or LongTermMemoryService()

    def analyze(self, payload: AnalyzeRequest, app_user_id: UUID | None = None) -> AnalyzeResponse:
        question = payload.question.strip() or "最近 30 天销售额按天变化如何？"
        state = self._load_or_create(payload.conversation_id, app_user_id, question)
        self._append_message(state, role="user", content=question)
        refresh_working_memory(state)

        if app_user_id is not None:
            memory_confirmation = self.long_term_memory_service.handle_explicit_preference(app_user_id, question, state.id)
            if memory_confirmation:
                state.pending_clarification = None
                state.status = "active"
                state.current_analysis = CurrentAnalysis(original_question=question, stage="completed", updated_at=_now())
                return self._finish(state, _memory_confirmation_response(question, memory_confirmation))

        intent: ParsedQuestionIntent | None = None
        if state.pending_clarification:
            resolution = resolve_followup(question, state.pending_clarification)
            if resolution.decision == "cancel":
                state.pending_clarification = None
                state.status = "cancelled"
                state.current_analysis = CurrentAnalysis(
                    original_question=question,
                    stage="cancelled",
                    updated_at=_now(),
                )
                response = _cancelled_response(question)
                return self._finish(state, response)
            if resolution.decision == "still_pending":
                state.pending_clarification = resolution.pending
                response = _pending_response(question, state.pending_clarification.clarification if resolution.pending else "请补充需要查询的指标。")
                return self._finish(state, response)
            if resolution.decision == "new_question":
                state.pending_clarification = None
                state.status = "active"
            intent = resolution.intent

        long_term_context = self.long_term_memory_service.context_for(app_user_id, question)
        conversation_context = "\n\n".join(item for item in (long_term_context, build_working_context(state)) if item)
        intent = intent or parse_question_intent(question, conversation_context=conversation_context)
        intent = apply_semantic_resolution(intent)
        intent = apply_clarification_policy(intent)
        if intent.needs_clarification:
            state.pending_clarification = pending_from_intent(intent)
            state.status = "waiting_for_clarification"
            state.current_analysis = CurrentAnalysis(
                original_question=intent.original_question,
                query_spec=intent.query_spec,
                stage="waiting_for_clarification",
                updated_at=_now(),
            )
            return self._finish(state, present_clarification_response(question, intent, latency_ms=0))

        state.pending_clarification = None
        state.status = "active"
        state.current_analysis = CurrentAnalysis(
            original_question=intent.original_question,
            query_spec=intent.query_spec,
            stage="executing",
            updated_at=_now(),
        )
        response = run_analysis_graph(intent.original_question, app_user_id=app_user_id, parsed_intent=intent)
        if not response.sql and response.source.security != "未生成 SQL，等待用户确认":
            state.current_analysis = state.current_analysis.model_copy(update={"stage": "completed", "updated_at": _now()})
            self._finish(state, _analysis_failure_response(question))
            raise AnalysisUnavailableError("分析服务暂时无法生成可执行查询，请稍后重试。")
        state.current_analysis = state.current_analysis.model_copy(update={"stage": "completed", "updated_at": _now()})
        return self._finish(state, response)

    def list_conversations(self, app_user_id: UUID | None, limit: int = 20) -> list[ConversationSummary]:
        return [state.summary() for state in self.conversation_store.list_for_owner(app_user_id, min(max(limit, 1), 100))]

    def get_conversation(self, conversation_id: UUID, app_user_id: UUID | None) -> ConversationDetail:
        state = self.conversation_store.get(conversation_id)
        if state is None or state.owner_id != app_user_id:
            raise HTTPException(status_code=404, detail="会话不存在")
        return state.detail()

    def claim_development_conversations(self, app_user_id: UUID) -> int:
        return self.conversation_store.claim_development_conversations(app_user_id)

    def _load_or_create(self, conversation_id: UUID | None, app_user_id: UUID | None, question: str) -> ConversationState:
        if conversation_id is None:
            now = _now()
            return ConversationState(id=uuid4(), owner_id=app_user_id, title=question[:80], created_at=now, updated_at=now)
        state = self.conversation_store.get(conversation_id)
        if state is None or state.owner_id != app_user_id:
            raise HTTPException(status_code=404, detail="会话不存在")
        return state

    def _finish(self, state: ConversationState, response: AnalyzeResponse) -> AnalyzeResponse:
        response = response.model_copy(
            update={
                "conversation_id": state.id,
                "pending_clarification": state.pending_clarification is not None,
                "conversation_status": state.status,
            }
        )
        self._append_message(state, role="assistant", content=response.summary, response=_response_preview(response))
        refresh_working_memory(state)
        state.updated_at = _now()
        self.conversation_store.save(state)
        return response

    def _append_message(self, state: ConversationState, *, role: str, content: str, response: dict | None = None) -> None:
        state.messages.append(ConversationMessage(id=uuid4(), role=role, content=content, created_at=_now(), response=response))
        state.messages = state.messages[-settings.conversation_message_limit:]
        state.updated_at = _now()


def _response_preview(response: AnalyzeResponse) -> dict:
    return {
        "summary": response.summary,
        "metrics": [item.model_dump() for item in response.metrics],
        "status": response.conversation_status,
        "failure": response.source.security == "未生成 SQL，已保存失败记录",
    }


def _pending_response(question: str, clarification: str) -> AnalyzeResponse:
    return AnalyzeResponse(
        question=question, path="cold_path", summary=clarification, sql="", metrics=[], rows=[],
        source={"dataset": "Olist 巴西电商公开数据集 + 合成增强数据", "tables": [], "fields": [], "metricDefinition": "等待补充条件", "range": "等待用户确认", "returnedRows": 0, "queryTime": "0ms", "security": "未生成 SQL，等待用户确认"},
        trace={"toolCalls": 0, "modelCalls": 0, "memoryCandidates": 0, "totalTime": "0ms"},
        steps=[{"name": "等待确认", "status": "已跳过", "time": "--"}],
    )


def _cancelled_response(question: str) -> AnalyzeResponse:
    return _pending_response(question, "已取消当前分析。你可以随时提出新的数据问题。").model_copy(update={"conversation_status": "cancelled"})


def _memory_confirmation_response(question: str, summary: str) -> AnalyzeResponse:
    return AnalyzeResponse(
        question=question, path="cold_path", summary=summary, sql="", metrics=[], rows=[],
        source={"dataset": "用户长期偏好", "tables": [], "fields": [], "metricDefinition": "显式偏好", "range": "长期生效", "returnedRows": 0, "queryTime": "0ms", "security": "未生成 SQL，已更新用户偏好"},
        trace={"toolCalls": 1, "modelCalls": 0, "memoryCandidates": 0, "totalTime": "0ms"},
        steps=[{"name": "更新长期偏好", "status": "已完成", "time": "0ms"}],
    )


def _analysis_failure_response(question: str) -> AnalyzeResponse:
    return AnalyzeResponse(
        question=question,
        path="cold_path",
        summary="本次分析未生成符合业务口径和安全规则的查询，已保存到会话历史。请稍后重试。",
        sql="",
        metrics=[],
        rows=[],
        source={"dataset": "Olist 巴西电商公开数据集 + 合成增强数据", "tables": [], "fields": [], "metricDefinition": "安全失败摘要", "range": "等待重试", "returnedRows": 0, "queryTime": "0ms", "security": "未生成 SQL，已保存失败记录"},
        trace={"toolCalls": 0, "modelCalls": 0, "memoryCandidates": 0, "totalTime": "0ms"},
        steps=[{"name": "保存失败会话", "status": "已完成", "time": "0ms"}],
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)
