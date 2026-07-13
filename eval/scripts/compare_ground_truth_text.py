"""对照外部问答文本、数据库真值集和认证评测报告。

脚本只生成数据集/质量摘要，不调用模型、不执行 SQL，也不读取或输出认证密码。
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEXT = Path(r"C:\Users\admin\Desktop\新建 文本文档.txt")
DEFAULT_DATASET = ROOT / "eval" / "datasets" / "database_ground_truth_questions.jsonl"
DEFAULT_EVAL_REPORT = ROOT / "eval" / "reports" / "post_upgrade_full_eval.json"
DEFAULT_OUTPUT = ROOT / "eval" / "reports" / "ground_truth_text_alignment.json"


def _normalize(value: str) -> str:
    """只消除人工文本中的格式差异，保留业务答案内容。"""
    text = str(value or "").replace("；", ";").replace("，", ",")
    text = re.sub(r"\s+", "", text).strip().lower()
    return text


def parse_text(path: Path) -> list[dict[str, str]]:
    """解析“问题？答案”行，忽略章节标题和可选的人工编号。"""
    rows: list[dict[str, str]] = []
    pattern = re.compile(r"^(?:\d+\.\s*)?(.+?[？?])\s*(.*)$")
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if not match:
            continue
        question, answer = match.groups()
        rows.append({"question": question.strip(), "answer": answer.strip()})
    return rows


def load_dataset(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        if raw_line.strip():
            rows.append(json.loads(raw_line))
    return rows


def compare_text_and_dataset(
    text_rows: list[dict[str, str]], dataset_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    question_mismatches: list[dict[str, Any]] = []
    answer_mismatches: list[dict[str, Any]] = []
    mode_mismatches: list[dict[str, Any]] = []
    count = min(len(text_rows), len(dataset_rows))
    for index in range(count):
        text_row = text_rows[index]
        dataset_row = dataset_rows[index]
        case_id = str(dataset_row.get("id") or f"line_{index + 1:03d}")
        if text_row["question"] != str(dataset_row.get("question") or ""):
            question_mismatches.append(
                {
                    "index": index + 1,
                    "id": case_id,
                    "text_question": text_row["question"],
                    "dataset_question": dataset_row.get("question", ""),
                }
            )
        dataset_answer = str(dataset_row.get("expected_answer") or "")
        # 归一化仅用于识别千分位/中文分隔符等排版差异，报告同时保留原值。
        if _normalize(text_row["answer"]) != _normalize(dataset_answer):
            answer_mismatches.append(
                {
                    "index": index + 1,
                    "id": case_id,
                    "text_answer": text_row["answer"],
                    "dataset_answer": dataset_answer,
                }
            )
        if dataset_row.get("result_match_mode", "tokens") in {"empty", "skip"}:
            expected_mode = str(dataset_row.get("result_match_mode"))
            # 外部文本使用自然语言描述；此处只记录应人工确认的特殊模式。
            mode_mismatches.append(
                {
                    "index": index + 1,
                    "id": case_id,
                    "dataset_mode": expected_mode,
                    "text_answer": text_row["answer"],
                }
            )
    missing_expected_tables = [
        str(row.get("id") or f"line_{index + 1:03d}")
        for index, row in enumerate(dataset_rows)
        if not list(row.get("expected_tables") or [])
    ]
    missing_expected_keywords = [
        str(row.get("id") or f"line_{index + 1:03d}")
        for index, row in enumerate(dataset_rows)
        if not list(row.get("expected_keywords") or [])
    ]
    return {
        "text_case_count": len(text_rows),
        "dataset_case_count": len(dataset_rows),
        "count_match": len(text_rows) == len(dataset_rows),
        "expected_case_count": 50,
        "coverage_match": len(text_rows) == len(dataset_rows) == 50,
        "question_mismatch_count": len(question_mismatches),
        "question_mismatches": question_mismatches,
        "answer_mismatch_count": len(answer_mismatches),
        "answer_mismatches": answer_mismatches,
        "special_result_cases": mode_mismatches,
        "special_result_case_count": len(mode_mismatches),
        "dataset_metadata": {
            "missing_expected_tables_count": len(missing_expected_tables),
            "missing_expected_tables_case_ids": missing_expected_tables,
            "missing_expected_keywords_count": len(missing_expected_keywords),
            "missing_expected_keywords_case_ids": missing_expected_keywords,
            "complete": not missing_expected_tables and not missing_expected_keywords,
        },
    }


def _primary_failure(case: dict[str, Any]) -> str:
    """为每个 case 选择一个可行动的主失败类别，避免重复计数。"""
    status_code = int(case.get("status_code") or 0)
    if status_code in {401, 403}:
        return "auth_or_permission"
    if status_code and status_code != 200:
        return "http_or_application_error"
    if not bool(case.get("has_sql")):
        return "empty_sql"
    if not bool(case.get("guard_passed")):
        return "guard_blocked"
    if case.get("missing_tables"):
        return "missing_table"
    if case.get("missing_keywords"):
        return "missing_sql_semantics"
    if case.get("forbidden_keyword_hits"):
        return "forbidden_sql_keyword"
    if case.get("answer_match") is False:
        return "answer_mismatch"
    if not bool(case.get("strict_ok")):
        return "other_strict_assertion"
    if not bool(case.get("ok")):
        return "execution_failure"
    return "ok"


def classify_eval_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": path.as_posix(), "available": False, "reason": "报告不存在"}
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    cases = list(report.get("cases") or [])
    categories = Counter(_primary_failure(case) for case in cases)
    by_category: dict[str, dict[str, Any]] = {}
    for case in cases:
        bucket = _primary_failure(case)
        item = by_category.setdefault(bucket, {"count": 0, "case_ids": []})
        item["count"] += 1
        item["case_ids"].append(case.get("id"))
    return {
        "path": path.as_posix(),
        "available": True,
        "generated_at": report.get("generated_at"),
        "dataset": report.get("dataset"),
        "summary": {
            key: report.get(key)
            for key in (
                "total",
                "success_count",
                "strict_success_count",
                "execution_success_rate",
                "strict_success_rate",
                "answer_checked_count",
                "answer_match_count",
                "answer_match_rate",
                "average_latency_ms",
            )
        },
        "case_count": len(cases),
        "failure_classification": dict(sorted(by_category.items())),
        "failure_classification_counts": dict(sorted(categories.items())),
    }


def build_report(text_path: Path, dataset_path: Path, eval_report_path: Path) -> dict[str, Any]:
    text_rows = parse_text(text_path)
    dataset_rows = load_dataset(dataset_path)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_text": str(text_path),
        "dataset_path": str(dataset_path),
        "text_dataset_alignment": compare_text_and_dataset(text_rows, dataset_rows),
        "evaluation_report": classify_eval_report(eval_report_path),
        "security": {
            "credentials_read": False,
            "sql_executed": False,
            "model_called": False,
            "raw_sql_or_prompt_recorded": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="核验外部数据库问答文本与评测集")
    parser.add_argument("--text", type=Path, default=DEFAULT_TEXT)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--eval-report", type=Path, default=DEFAULT_EVAL_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build_report(args.text, args.dataset, args.eval_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    alignment = report["text_dataset_alignment"]
    print(
        "alignment completed: "
        f"text={alignment['text_case_count']}, "
        f"dataset={alignment['dataset_case_count']}, "
        f"question_mismatches={alignment['question_mismatch_count']}, "
        f"answer_mismatches={alignment['answer_mismatch_count']}, "
        f"report={args.output}"
    )


if __name__ == "__main__":
    main()
