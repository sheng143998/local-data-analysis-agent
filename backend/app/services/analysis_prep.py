"""分析前置准备：意图解析（LLM）与检索（embedding + DB）并行（计划 2b）。

两者没有数据依赖——意图解析只需要问题与会话上下文，指标/schema 召回只需要
问题文本与向量；语义契约与查询计划在意图完成后才合并进上下文（便宜的 DB 操作，
由 build_retrieval_context 在图内完成）。并行后冷路径可省去一段约等于
min(意图 LLM 耗时, embedding+检索耗时) 的墙钟时间。
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from backend.app.core.config import settings
from backend.app.schemas.retrieval import MetricContext, SchemaColumnContext
from backend.app.tools.metric_retriever import retrieve_metrics
from backend.app.tools.question_intent_parser import ParsedQuestionIntent, parse_question_intent
from backend.app.tools.schema_retriever import retrieve_schema
from backend.app.tools.vector_retrieval import embed_question

logger = logging.getLogger("backend.analysis_prep")


@dataclass
class PrecomputedRetrieval:
    """与意图并行完成的检索产物；图内 _retrieve_context_node 直接复用。"""

    question_vector: list[float] = field(default_factory=list)
    metrics: list[MetricContext] = field(default_factory=list)
    schema_columns: list[SchemaColumnContext] = field(default_factory=list)


def _preretrieve(question: str) -> PrecomputedRetrieval:
    question_vector = embed_question(question)
    metrics = retrieve_metrics(question, question_vector=question_vector)
    schema_columns = retrieve_schema(question, metrics, question_vector=question_vector)
    return PrecomputedRetrieval(
        question_vector=question_vector,
        metrics=metrics,
        schema_columns=schema_columns,
    )


def prepare_analysis_inputs(
    question: str,
    conversation_context: str = "",
    intent_parser=None,
) -> tuple[ParsedQuestionIntent, PrecomputedRetrieval | None]:
    """并行执行意图解析与检索预取。

    intent_parser 由调用方注入（默认用本模块导入的 parse_question_intent），
    保证服务层对解析器的替换/打桩依旧生效。检索分支任何失败都不影响主流程
    （返回 None，图内回退为串行检索）；意图分支的异常照常抛出。
    """
    parser = intent_parser or parse_question_intent
    if not settings.parallel_intent_retrieval:
        return parser(question, conversation_context=conversation_context), None

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="analysis-prep") as executor:
        intent_future = executor.submit(
            parser, question, conversation_context=conversation_context
        )
        retrieval_future = executor.submit(_preretrieve, question)
        intent = intent_future.result()
        try:
            precomputed = retrieval_future.result()
        except Exception:  # noqa: BLE001 - 预取失败回退串行路径
            logger.warning("parallel retrieval prefetch failed; falling back", exc_info=True)
            precomputed = None
    return intent, precomputed
