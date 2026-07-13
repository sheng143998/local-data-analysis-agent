from __future__ import annotations

import json
import os
import re
from argparse import ArgumentParser
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings


DATASET_PATH = ROOT / "eval" / "datasets" / "standard_questions.jsonl"
REGRESSION_DATASET_PATH = ROOT / "eval" / "datasets" / "regression_questions.jsonl"
DATABASE_GROUND_TRUTH_DATASET_PATH = ROOT / "eval" / "datasets" / "database_ground_truth_questions.jsonl"
REPORT_PATH = ROOT / "eval" / "reports" / "latest_eval_report.json"


@dataclass(frozen=True)
class EvalCase:
    id: str
    category: str
    question: str
    expected_tables: list[str]
    expected_keywords: list[str]
    forbidden_keywords: list[str] = field(default_factory=list)
    expected_answer: str = ""
    expected_result_tokens: list[str] = field(default_factory=list)
    result_match_mode: str = "tokens"


@dataclass(frozen=True)
class EvalCaseResult:
    id: str
    category: str
    question: str
    ok: bool
    path: str
    status_code: int
    latency_ms: int
    has_sql: bool
    guard_passed: bool
    memory_hit: bool
    expected_table_hits: list[str]
    expected_keyword_hits: list[str]
    missing_tables: list[str]
    missing_keywords: list[str]
    forbidden_keyword_hits: list[str]
    table_match: bool
    keyword_match: bool
    forbidden_match: bool
    strict_ok: bool
    returned_rows: int
    expected_answer: str = ""
    actual_answer: str = ""
    answer_match: bool | None = None
    answer_mismatch: str = ""
    run_id: str | None = None
    run_detail_path: str = ""
    run_trace_summary: dict[str, Any] = field(default_factory=dict)
    error: str = ""


AnalyzeFunc = Callable[[str], tuple[int, dict[str, Any]]]


class EvaluationConfigurationError(RuntimeError):
    """评测环境缺少必要配置时中止，避免把环境问题误记为模型失败。"""


def load_cases(path: Path = DATASET_PATH) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        cases.append(
            EvalCase(
                id=payload["id"],
                category=payload["category"],
                question=payload["question"],
                expected_tables=list(payload.get("expected_tables") or []),
                expected_keywords=list(payload.get("expected_keywords") or []),
                forbidden_keywords=list(payload.get("forbidden_keywords") or []),
                expected_answer=str(payload.get("expected_answer") or ""),
                expected_result_tokens=list(payload.get("expected_result_tokens") or []),
                result_match_mode=str(payload.get("result_match_mode") or "tokens"),
            )
        )
    return cases


def load_regression_cases(path: Path = REGRESSION_DATASET_PATH) -> list[EvalCase]:
    return load_cases(path)


def load_database_ground_truth_cases(
    path: Path = DATABASE_GROUND_TRUTH_DATASET_PATH,
) -> list[EvalCase]:
    return load_cases(path)


def run_cases(cases: list[EvalCase], analyze: AnalyzeFunc) -> list[EvalCaseResult]:
    results: list[EvalCaseResult] = []
    for case in cases:
        started = perf_counter()
        try:
            status_code, body = analyze(case.question)
            latency_ms = int((perf_counter() - started) * 1000)
            sql = str(body.get("sql") or "")
            source = body.get("source") or {}
            run_id, run_detail_path, run_trace_summary = _extract_eval_run_trace(body)
            table_hits = [table for table in case.expected_tables if table in sql]
            keyword_hits = [
                keyword for keyword in case.expected_keywords if keyword.lower() in sql.lower()
            ]
            missing_tables = [table for table in case.expected_tables if table not in table_hits]
            missing_keywords = [
                keyword for keyword in case.expected_keywords if keyword not in keyword_hits
            ]
            forbidden_keyword_hits = [
                keyword
                for keyword in case.forbidden_keywords
                if keyword.lower() in sql.lower()
            ]
            has_sql = bool(sql.strip())
            guard_passed = "SQL Guard" in str(source.get("security") or "")
            ok = status_code == 200 and has_sql and guard_passed
            table_match = len(missing_tables) == 0
            keyword_match = len(missing_keywords) == 0
            forbidden_match = len(forbidden_keyword_hits) == 0
            actual_answer = _serialize_rows(body.get("rows"))
            answer_match, answer_mismatch = _match_expected_answer(case, body.get("rows"))
            strict_ok = (
                ok
                and table_match
                and keyword_match
                and forbidden_match
                and (answer_match is not False)
            )
            results.append(
                EvalCaseResult(
                    id=case.id,
                    category=case.category,
                    question=case.question,
                    ok=ok,
                    path=str(body.get("path") or ""),
                    status_code=status_code,
                    latency_ms=latency_ms,
                    has_sql=has_sql,
                    guard_passed=guard_passed,
                    memory_hit=str(body.get("path") or "") == "fast_path",
                    expected_table_hits=table_hits,
                    expected_keyword_hits=keyword_hits,
                    missing_tables=missing_tables,
                    missing_keywords=missing_keywords,
                    forbidden_keyword_hits=forbidden_keyword_hits,
                    table_match=table_match,
                    keyword_match=keyword_match,
                    forbidden_match=forbidden_match,
                    strict_ok=strict_ok,
                    returned_rows=int(source.get("returnedRows") or 0),
                    expected_answer=case.expected_answer,
                    actual_answer=actual_answer,
                    answer_match=answer_match,
                    answer_mismatch=answer_mismatch,
                    run_id=run_id,
                    run_detail_path=run_detail_path,
                    run_trace_summary=run_trace_summary,
                    error=str(body.get("summary") or "") if not ok else "",
                )
            )
        except Exception as exc:  # noqa: BLE001 - eval runner must capture failures
            results.append(
                EvalCaseResult(
                    id=case.id,
                    category=case.category,
                    question=case.question,
                    ok=False,
                    path="error",
                    status_code=0,
                    latency_ms=int((perf_counter() - started) * 1000),
                    has_sql=False,
                    guard_passed=False,
                    memory_hit=False,
                    expected_table_hits=[],
                    expected_keyword_hits=[],
                    missing_tables=case.expected_tables,
                    missing_keywords=case.expected_keywords,
                    forbidden_keyword_hits=[],
                    table_match=False,
                    keyword_match=False,
                    forbidden_match=False,
                    strict_ok=False,
                    returned_rows=0,
                    expected_answer=case.expected_answer,
                    actual_answer="",
                    answer_match=False if case.expected_answer else None,
                    answer_mismatch="评测执行异常，未获得可比较结果" if case.expected_answer else "",
                    run_id=None,
                    run_detail_path="",
                    run_trace_summary={},
                    error=str(exc),
                )
            )
    return results


def summarize_results(results: list[EvalCaseResult]) -> dict[str, Any]:
    total = len(results)
    success_count = sum(1 for result in results if result.ok)
    strict_success_count = sum(1 for result in results if result.strict_ok)
    sql_success_count = sum(1 for result in results if result.has_sql)
    memory_hit_count = sum(1 for result in results if result.memory_hit)
    reuse_success_count = sum(1 for result in results if result.ok and result.path == "fast_path")
    table_match_count = sum(1 for result in results if result.table_match)
    keyword_match_count = sum(1 for result in results if result.keyword_match)
    forbidden_match_count = sum(1 for result in results if result.forbidden_match)
    answer_checked_results = [result for result in results if result.answer_match is not None]
    answer_match_count = sum(1 for result in answer_checked_results if result.answer_match)
    path_counts: dict[str, int] = {}
    for result in results:
        path_counts[result.path] = path_counts.get(result.path, 0) + 1
    assertion_failures = [
        result
        for result in results
        if result.ok and not result.strict_ok
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "success_count": success_count,
        "strict_success_count": strict_success_count,
        "execution_success_rate": _rate(success_count, total),
        "strict_success_rate": _rate(strict_success_count, total),
        "sql_generation_success_rate": _rate(sql_success_count, total),
        "table_match_rate": _rate(table_match_count, total),
        "keyword_match_rate": _rate(keyword_match_count, total),
        "forbidden_match_rate": _rate(forbidden_match_count, total),
        "answer_checked_count": len(answer_checked_results),
        "answer_match_count": answer_match_count,
        "answer_match_rate": _rate(answer_match_count, len(answer_checked_results)),
        "memory_hit_rate": _rate(memory_hit_count, total),
        "reuse_success_rate": _rate(reuse_success_count, total),
        "average_latency_ms": round(
            sum(result.latency_ms for result in results) / total if total else 0
        ),
        "path_counts": path_counts,
        "failures": [asdict(result) for result in results if not result.ok],
        "assertion_failures": [asdict(result) for result in assertion_failures],
        "assertion_failure_summary": _assertion_failure_summary(assertion_failures),
        "cases": [asdict(result) for result in results],
    }


def write_report(report: dict[str, Any], path: Path = REPORT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def analyze_with_test_client(question: str) -> tuple[int, dict[str, Any]]:
    client = TestClient(app)
    authenticate_evaluation_client(client)
    return _analyze_with_client(client, question)


def create_test_client_analyzer() -> AnalyzeFunc:
    """每批评测只登录一次，避免为每个 case 生成无意义会话记录。"""
    client = TestClient(app)
    authenticate_evaluation_client(client)

    def analyze(question: str) -> tuple[int, dict[str, Any]]:
        return _analyze_with_client(client, question)

    return analyze


def _analyze_with_client(client: TestClient, question: str) -> tuple[int, dict[str, Any]]:
    response = client.post("/api/analyze", json={"question": question})
    body = response.json()
    if isinstance(body, dict):
        run_id = _find_latest_run_id(client, question)
        if run_id:
            body["_eval_run_id"] = run_id
            body["_eval_run_detail_path"] = f"/api/runs/{run_id}"
            body["_eval_run_trace_summary"] = _fetch_run_trace_summary(client, run_id)
    return response.status_code, body


def authenticate_evaluation_client(
    client: TestClient,
    *,
    auth_required: bool | None = None,
    environment: dict[str, str] | None = None,
) -> None:
    """鉴权开启时以专用账号登录，禁止通过关闭鉴权伪造评测成功。"""
    if not (settings.auth_required if auth_required is None else auth_required):
        return
    values = os.environ if environment is None else environment
    email = str(values.get("EVAL_AUTH_EMAIL") or "").strip()
    password = str(values.get("EVAL_AUTH_PASSWORD") or "")
    if not email or not password:
        raise EvaluationConfigurationError(
            "AUTH_REQUIRED=true 时必须配置 EVAL_AUTH_EMAIL 和 EVAL_AUTH_PASSWORD；"
            "评测不会自动注册或创建用户。"
        )
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        raise EvaluationConfigurationError(
            f"评测账号登录失败（HTTP {response.status_code}）。请检查 EVAL_AUTH_EMAIL、"
            "EVAL_AUTH_PASSWORD 与账号状态；不会把该错误计入模型质量报告。"
        )


def main() -> None:
    parser = ArgumentParser(description="运行本地数据分析 Agent 评测")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH, help="JSONL 评测集路径")
    args = parser.parse_args()
    cases = load_cases(args.dataset)
    try:
        analyze = create_test_client_analyzer()
    except EvaluationConfigurationError as exc:
        raise SystemExit(f"eval blocked: {exc}") from exc
    results = run_cases(cases, analyze)
    report = summarize_results(results)
    write_report(report)
    print(
        "eval completed: "
        f"{report['success_count']}/{report['total']} ok, "
        f"execution_success_rate={report['execution_success_rate']:.2%}, "
        f"strict_success_rate={report['strict_success_rate']:.2%}, "
        f"answer_match_rate={report['answer_match_rate']:.2%}, "
        f"report={REPORT_PATH}"
    )


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0
    return round(numerator / denominator, 4)


def _match_expected_answer(case: EvalCase, rows: Any) -> tuple[bool | None, str]:
    if not case.expected_answer or case.result_match_mode == "skip":
        return None, ""
    normalized_actual = _normalize_answer(_serialize_rows(rows))
    if case.result_match_mode == "empty":
        if not normalized_actual:
            return True, ""
        return False, "期望空结果集，但接口返回了数据"
    token_source = case.expected_result_tokens or re.split(r"[；;]", case.expected_answer)
    expected_tokens = [
        _normalize_answer(token)
        for token in token_source
        if _normalize_answer(token)
    ]
    missing = [token for token in expected_tokens if token not in normalized_actual]
    if not missing:
        return True, ""
    return False, f"未匹配期望结果片段：{'；'.join(missing)}"


def _serialize_rows(rows: Any) -> str:
    if not isinstance(rows, list):
        return ""
    serialized_rows: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            serialized_rows.append(" ".join(str(value) for value in row.values() if value is not None))
        elif row is not None:
            serialized_rows.append(str(row))
    return "；".join(serialized_rows)


def _normalize_answer(value: str) -> str:
    text = str(value).strip().lower()
    text = text.replace(",", "").replace("，", "")
    text = text.replace("¥", "").replace("元", "").replace("天", "").replace("分", "")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"(\d+)\.0+(?=\D|$)", r"\1", text)
    return text


def _extract_eval_run_trace(body: dict[str, Any]) -> tuple[str | None, str, dict[str, Any]]:
    trace_summary = body.get("_eval_run_trace_summary")
    safe_trace_summary = trace_summary if isinstance(trace_summary, dict) else {}
    run_id = body.get("_eval_run_id")
    if not run_id:
        return None, "", safe_trace_summary
    run_id_text = str(run_id)
    run_detail_path = str(body.get("_eval_run_detail_path") or f"/api/runs/{run_id_text}")
    return run_id_text, run_detail_path, safe_trace_summary


def _find_latest_run_id(client: TestClient, question: str) -> str | None:
    try:
        response = client.get("/api/runs?limit=5")
        if response.status_code != 200:
            return None
        runs = response.json()
    except Exception:
        return None
    if not isinstance(runs, list):
        return None
    for run in runs:
        if not isinstance(run, dict):
            continue
        if run.get("user_question") == question and run.get("id"):
            return str(run["id"])
    return None


def _fetch_run_trace_summary(client: TestClient, run_id: str) -> dict[str, Any]:
    try:
        response = client.get(f"/api/runs/{run_id}")
        if response.status_code != 200:
            return {}
        detail = response.json()
    except Exception:
        return {}
    return _build_run_trace_summary(detail)


def _build_run_trace_summary(run_detail: dict[str, Any]) -> dict[str, Any]:
    tool_calls = run_detail.get("tool_calls")
    if not isinstance(tool_calls, list):
        return {}
    tools = {
        tool.get("tool_name"): tool
        for tool in tool_calls
        if isinstance(tool, dict) and tool.get("tool_name")
    }
    context = _output_payload(tools, "context_builder.build_retrieval_context")
    generation = _output_payload(tools, "analysis_graph.select_generated_sql")
    guard = _output_payload(tools, "sql_validation_tools.guard_sql")
    memory_plan = _output_payload(tools, "sql_memory_tools.plan_sql_reuse")
    timings = _output_payload(tools, "analysis_graph.pipeline_timings")
    context_table_coverage = generation.get("context_table_coverage")
    summary = {
        "context_tables": _string_list(context.get("tables")),
        "context_fields_sample": _string_list(context.get("fields_sample")),
        "metric_count": _safe_int(context.get("metric_count")),
        "schema_column_count": _safe_int(context.get("schema_column_count")),
        "relationship_count": _safe_int(context.get("relationship_count")),
        "generation_path": str(generation.get("generation_path") or ""),
        "generation_warning_count": _safe_int(generation.get("warning_count")),
        "generation_warnings": _string_list(generation.get("warnings")),
        "guard_status": str(guard.get("guard_status") or ""),
        "guard_warning_count": _safe_int(guard.get("warning_count")),
        "guard_warnings": _string_list(guard.get("warnings")),
        "guard_error_count": _safe_int(guard.get("error_count")),
        "guard_errors": _string_list(guard.get("errors")),
        "memory_path_type": str(memory_plan.get("path_type") or ""),
        "memory_reuse_type": str(memory_plan.get("reuse_type") or ""),
        "memory_hit": bool(memory_plan.get("memory_hit") or False),
        "memory_score": memory_plan.get("score"),
        "node_timings_ms": timings.get("node_timings_ms") if isinstance(timings.get("node_timings_ms"), dict) else {},
        "total_latency_ms": _safe_int(timings.get("total_latency_ms")),
        "slowest_node": timings.get("slowest_node") if isinstance(timings.get("slowest_node"), dict) else {},
    }
    if isinstance(context_table_coverage, dict) and context_table_coverage:
        summary["context_table_coverage"] = context_table_coverage
    return summary


def _output_payload(tools: dict[str, Any], tool_name: str) -> dict[str, Any]:
    tool = tools.get(tool_name)
    if not isinstance(tool, dict):
        return {}
    payload = tool.get("output_payload")
    return payload if isinstance(payload, dict) else {}


def _assertion_failure_summary(results: list[EvalCaseResult]) -> dict[str, Any]:
    missing_table_counts: dict[str, int] = {}
    forbidden_keyword_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    path_counts: dict[str, int] = {}
    context_status_counts: dict[tuple[str, str], int] = {}

    for result in results:
        category_counts[result.category] = category_counts.get(result.category, 0) + 1
        path_counts[result.path] = path_counts.get(result.path, 0) + 1
        context_tables = set(_string_list(result.run_trace_summary.get("context_tables")))
        for table in result.missing_tables:
            missing_table_counts[table] = missing_table_counts.get(table, 0) + 1
            status = "present_in_context" if table in context_tables else "missing_from_context"
            key = (table, status)
            context_status_counts[key] = context_status_counts.get(key, 0) + 1
        for keyword in result.forbidden_keyword_hits:
            forbidden_keyword_counts[keyword] = forbidden_keyword_counts.get(keyword, 0) + 1

    return {
        "total": len(results),
        "by_missing_table": _sorted_count_items(missing_table_counts),
        "by_forbidden_keyword": _sorted_count_items(forbidden_keyword_counts),
        "by_missing_table_context_status": _sorted_context_status_items(context_status_counts),
        "by_category": _sorted_count_items(category_counts),
        "by_path": _sorted_count_items(path_counts),
        "case_ids": [result.id for result in results],
    }


def _sorted_count_items(counts: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {"name": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _sorted_context_status_items(counts: dict[tuple[str, str], int]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, int | str]] = {}
    for (table, status), count in counts.items():
        item = grouped.setdefault(
            table,
            {
                "name": table,
                "missing_from_context": 0,
                "present_in_context": 0,
            },
        )
        item[status] = int(item[status]) + count
    return sorted(
        grouped.values(),
        key=lambda item: (
            -int(item["missing_from_context"]),
            -int(item["present_in_context"]),
            str(item["name"]),
        ),
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    main()
