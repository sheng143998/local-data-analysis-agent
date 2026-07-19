from datetime import datetime, timezone
from uuid import uuid4

from backend.app.schemas.runs import QueryRunDetail, ToolCallRecord
from backend.app.services.run_service import _build_debug_summary


def test_run_debug_summary_exposes_sql_candidates_from_admin_detail_only() -> None:
    run_id = uuid4()
    run = QueryRunDetail(
        id=run_id,
        user_question="2017 年每个月已支付订单的销售额和订单数分别是多少？",
        guard_status="blocked",
        execution_status="error",
        tool_calls=[
            ToolCallRecord(
                id=uuid4(),
                query_run_id=run_id,
                tool_name="analysis_graph.select_generated_sql",
                input_payload={},
                output_payload={
                    "generation_path": "model_error",
                    "sql_candidates": [
                        {
                            "stage": "generation",
                            "path": "model_generate",
                            "sql": "SELECT 1",
                            "warning_count": 2,
                            "reasoning": "不会被运行详情透出",
                        }
                    ],
                },
                status="success",
                created_at=datetime.now(timezone.utc),
            )
        ],
        created_at=datetime.now(timezone.utc),
    )

    summary = _build_debug_summary(run)

    assert summary["sql_generation"]["sql_candidates"] == [
        {
            "stage": "generation",
            "path": "model_generate",
            "sql": "SELECT 1",
            "warning_count": 2,
        }
    ]
    assert "sql_candidates" not in run.model_dump()
