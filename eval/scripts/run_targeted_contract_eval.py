"""重跑历史严格失败 SQL case，并加入稳定随机对照样本。"""

from __future__ import annotations

import json
import random
import sys
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from eval.scripts.run_eval import (  # noqa: E402
    EvalCase,
    create_test_client_analyzer,
    load_database_ground_truth_cases,
    run_cases,
    summarize_results,
)


DEFAULT_BASELINE = ROOT / "eval" / "reports" / "sql_model_replacement_full_eval_20260714.json"
DEFAULT_REPORT = ROOT / "eval" / "reports" / "targeted_contract_eval.json"
RANDOM_SEED = 20260718


def main() -> None:
    parser = ArgumentParser(description="运行历史失败与稳定随机 SQL 合同评测")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--random-count", type=int, default=5)
    args = parser.parse_args()

    baseline = _load_baseline(args.baseline)
    all_cases = {case.id: case for case in load_database_ground_truth_cases()}
    failed_ids = [str(item["id"]) for item in baseline["cases"] if not item.get("strict_ok", False)]
    successful_ids = [str(item["id"]) for item in baseline["cases"] if item.get("strict_ok", False)]
    random_ids = random.Random(RANDOM_SEED).sample(successful_ids, min(args.random_count, len(successful_ids)))
    selected_ids = list(dict.fromkeys([*failed_ids, *random_ids]))
    selected_cases: list[EvalCase] = [all_cases[case_id] for case_id in selected_ids if case_id in all_cases]

    analyzer = create_test_client_analyzer()
    results = run_cases(selected_cases, analyzer)
    report = summarize_results(results)
    report["selection"] = {
        "baseline": str(args.baseline),
        "baseline_strict_failure_ids": failed_ids,
        "stable_random_seed": RANDOM_SEED,
        "random_control_ids": random_ids,
        "selected_case_ids": selected_ids,
        "selected_case_count": len(selected_cases),
    }
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"targeted eval completed: {report['success_count']}/{report['total']} ok, "
        f"strict={report['strict_success_count']}/{report['total']}, "
        f"answers={report['answer_match_count']}/{report['answer_checked_count']}, "
        f"report={args.report}"
    )


def _load_baseline(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise SystemExit(f"baseline 报告缺少 cases：{path}")
    return payload


if __name__ == "__main__":
    main()
