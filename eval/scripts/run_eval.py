from __future__ import annotations

import json
from dataclasses import dataclass, asdict
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
    returned_rows: int
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
            trace = body.get("trace") or {}
            table_hits = [table for table in case.expected_tables if table in sql]
            keyword_hits = [
                keyword for keyword in case.expected_keywords if keyword.lower() in sql.lower()
            ]
            has_sql = bool(sql.strip())
            guard_passed = "SQL Guard" in str(source.get("security") or "")
            ok = status_code == 200 and has_sql and guard_passed
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
                    returned_rows=int(source.get("returnedRows") or 0),
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
                    returned_rows=0,
                    error=str(exc),
                )
            )
    return results


def summarize_results(results: list[EvalCaseResult]) -> dict[str, Any]:
    total = len(results)
    success_count = sum(1 for result in results if result.ok)
    sql_success_count = sum(1 for result in results if result.has_sql)
    memory_hit_count = sum(1 for result in results if result.memory_hit)
    reuse_success_count = sum(1 for result in results if result.ok and result.path == "fast_path")
    path_counts: dict[str, int] = {}
    for result in results:
        path_counts[result.path] = path_counts.get(result.path, 0) + 1
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "success_count": success_count,
        "execution_success_rate": _rate(success_count, total),
        "sql_generation_success_rate": _rate(sql_success_count, total),
        "memory_hit_rate": _rate(memory_hit_count, total),
        "reuse_success_rate": _rate(reuse_success_count, total),
        "average_latency_ms": round(
            sum(result.latency_ms for result in results) / total if total else 0
        ),
        "path_counts": path_counts,
        "failures": [asdict(result) for result in results if not result.ok],
        "cases": [asdict(result) for result in results],
    }


def write_report(report: dict[str, Any], path: Path = REPORT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def analyze_with_test_client(question: str) -> tuple[int, dict[str, Any]]:
    client = TestClient(app)
    response = client.post("/api/analyze", json={"question": question})
    return response.status_code, response.json()


def main() -> None:
    cases = load_cases()
    results = run_cases(cases, analyze_with_test_client)
    report = summarize_results(results)
    write_report(report)
    print(
        "eval completed: "
        f"{report['success_count']}/{report['total']} ok, "
        f"execution_success_rate={report['execution_success_rate']:.2%}, "
        f"report={REPORT_PATH}"
    )


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0
    return round(numerator / denominator, 4)


if __name__ == "__main__":
    main()
