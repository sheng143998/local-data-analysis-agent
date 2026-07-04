from __future__ import annotations

import json
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


DATASET_PATH = ROOT / "eval" / "datasets" / "standard_questions.jsonl"
REPORT_PATH = ROOT / "eval" / "reports" / "latest_eval_report.json"


@dataclass(frozen=True)
class EvalCase:
    id: str
    category: str
    question: str
    expected_tables: list[str]
    expected_keywords: list[str]


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
    table_match: bool
    keyword_match: bool
    strict_ok: bool
    returned_rows: int
    run_id: str | None = None
    run_detail_path: str = ""
    run_trace_summary: dict[str, Any] = field(default_factory=dict)
    error: str = ""


AnalyzeFunc = Callable[[str], tuple[int, dict[str, Any]]]


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
            )
        )
    return cases


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
            has_sql = bool(sql.strip())
            guard_passed = "SQL Guard" in str(source.get("security") or "")
            ok = status_code == 200 and has_sql and guard_passed
            table_match = len(missing_tables) == 0
            keyword_match = len(missing_keywords) == 0
            strict_ok = ok and table_match and keyword_match
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
                    table_match=table_match,
                    keyword_match=keyword_match,
                    strict_ok=strict_ok,
                    returned_rows=int(source.get("returnedRows") or 0),
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
                    table_match=False,
                    keyword_match=False,
                    strict_ok=False,
                    returned_rows=0,
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
    response = client.post("/api/analyze", json={"question": question})
    body = response.json()
    if isinstance(body, dict):
        run_id = _find_latest_run_id(client, question)
        if run_id:
            body["_eval_run_id"] = run_id
            body["_eval_run_detail_path"] = f"/api/runs/{run_id}"
            body["_eval_run_trace_summary"] = _fetch_run_trace_summary(client, run_id)
    return response.status_code, body


def main() -> None:
    cases = load_cases()
    results = run_cases(cases, analyze_with_test_client)
    report = summarize_results(results)
    write_report(report)
    print(
        "eval completed: "
        f"{report['success_count']}/{report['total']} ok, "
        f"execution_success_rate={report['execution_success_rate']:.2%}, "
        f"strict_success_rate={report['strict_success_rate']:.2%}, "
        f"report={REPORT_PATH}"
    )


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0
    return round(numerator / denominator, 4)


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

    return {
        "total": len(results),
        "by_missing_table": _sorted_count_items(missing_table_counts),
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
