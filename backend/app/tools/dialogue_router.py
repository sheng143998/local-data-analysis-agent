from typing import Literal

from pydantic import BaseModel

from backend.app.schemas.conversation import ConversationState


DialogueRole = Literal["general_chat", "data_analysis", "clarification", "explain_result", "unsupported"]


class DialogueDecision(BaseModel):
    role: DialogueRole
    reason: str


_DATA_TERMS = ("销售", "订单", "用户", "退款", "毛利", "复购", "支付", "数据", "金额", "客单", "趋势", "品类", "统计", "多少", "排行")
_OVERVIEW_ANALYSIS_TERMS = ("看看最近情况", "看下最近情况", "最近经营情况", "最近业务情况", "经营概览", "业务概览")
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
    # 业务概览请求缺少具体指标时也必须进入澄清，而不是由闲聊模型编造结论。
    if any(term in question for term in _OVERVIEW_ANALYSIS_TERMS):
        return DialogueDecision(role="data_analysis", reason="用户请求业务概览，后续由意图解析决定是否澄清")
    return DialogueDecision(role="general_chat", reason="非数据问题默认进入通用聊天")
