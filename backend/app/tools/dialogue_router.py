from typing import Literal

from pydantic import BaseModel

from backend.app.schemas.conversation import ConversationState


DialogueRole = Literal["general_chat", "data_analysis", "clarification", "explain_result", "unsupported"]


class DialogueDecision(BaseModel):
    role: DialogueRole
    reason: str


_DATA_TERMS = ("销售", "订单", "用户", "退款", "毛利", "复购", "支付", "数据", "金额", "客单", "趋势", "品类", "统计", "多少", "排行")
_EXPLAIN_TERMS = ("解释", "什么意思", "为什么", "结论", "刚才", "上个结果", "这个结果")
_UNSUPPORTED_TERMS = ("忽略之前", "系统提示词", "api key", "密钥", "执行 shell", "删除数据库")


def route_dialogue(question: str, state: ConversationState) -> DialogueDecision:
    """路由是 SQL 安全的第一道业务边界，默认不访问数据库。"""
    normalized = question.lower()
    if any(term in normalized for term in _UNSUPPORTED_TERMS):
        return DialogueDecision(role="unsupported", reason="请求涉及系统指令、密钥或越权操作")
    if state.pending_clarification is not None:
        return DialogueDecision(role="clarification", reason="当前会话正在等待业务条件补充")
    if any(term in question for term in _EXPLAIN_TERMS) and any(item.role == "assistant" for item in state.messages):
        return DialogueDecision(role="explain_result", reason="用户请求解释当前会话中的结果")
    if any(term in question for term in _DATA_TERMS):
        return DialogueDecision(role="data_analysis", reason="用户明确提出业务数据查询")
    return DialogueDecision(role="general_chat", reason="非数据问题默认进入通用聊天")
