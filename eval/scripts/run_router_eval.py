"""运行 Router 真实语义分类样本，报告不进入 Git。"""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = ROOT / "eval" / "reports" / "router_semantic_eval.json"
sys.path.insert(0, str(ROOT))

from backend.app.schemas.conversation import ConversationState, CurrentAnalysis
from backend.app.tools.dialogue_router import route_dialogue

CASES = [
    ("你好，介绍一下你能做什么", "general_chat", False),
    ("如何提升用户体验？", "general_chat", False),
    ("帮我把这段产品说明写得更简洁", "general_chat", False),
    ("RAG 和 Agent 有什么区别？", "general_chat", False),
    ("当前订单数是多少？", "data_analysis", False),
    ("本月退款率按天趋势如何？", "data_analysis", False),
    ("帮我看一下退款情况", "data_analysis", False),
    ("销售额最高的前 5 个品类是什么？", "data_analysis", False),
    ("看看最近经营情况", "data_analysis", False),
    ("解释刚才的这个结果为什么会这样", "explain_result", True),
]


def main() -> None:
    parser = ArgumentParser(description="运行 Router 真实语义分类评测")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    results: list[dict] = []
    for question, expected_role, has_completed_analysis in CASES:
        now = datetime.now(timezone.utc)
        state = ConversationState(
            id=uuid4(),
            title="Router 语义评测",
            created_at=now,
            updated_at=now,
        )
        if has_completed_analysis:
            state.current_analysis = CurrentAnalysis(
                original_question="本月订单数",
                stage="completed",
                updated_at=now,
            )
        decision = route_dialogue(question, state)
        results.append(
            {
                "question": question,
                "expected_role": expected_role,
                "actual_role": decision.role,
                "source": decision.source,
                "confidence": decision.confidence,
                "reason": decision.reason,
                "passed": decision.role == expected_role,
            }
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "passed": sum(1 for item in results if item["passed"]),
        "model_decision_count": sum(1 for item in results if item["source"] == "model"),
        "fallback_count": sum(1 for item in results if item["source"] == "fallback"),
        "deterministic_count": sum(1 for item in results if item["source"] == "deterministic"),
        "cases": results,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"router eval completed: {report['passed']}/{report['total']} passed, "
        f"model={report['model_decision_count']}, fallback={report['fallback_count']}, "
        f"report={args.report}"
    )


if __name__ == "__main__":
    main()
