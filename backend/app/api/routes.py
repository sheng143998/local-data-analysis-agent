import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.api.auth import router as auth_router
from backend.app.api.dependencies import get_current_principal
from backend.app.api.conversations import router as conversations_router
from backend.app.api.long_term_memories import router as long_term_memories_router
from backend.app.api.memories import router as memories_router
from backend.app.api.metrics import router as metrics_router
from backend.app.api.runs import router as runs_router
from backend.app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from backend.app.schemas.auth import AuthPrincipal
from backend.app.services.agent_service import AgentService, AnalysisUnavailableError


router = APIRouter()
agent_service = AgentService()
router.include_router(auth_router)
router.include_router(conversations_router)
router.include_router(long_term_memories_router)
router.include_router(memories_router)
router.include_router(metrics_router)
router.include_router(runs_router)


@router.get("/health")
def health() -> dict[str, str | bool]:
    return {"ok": True, "service": "local-data-analysis-agent", "version": "0.1.0"}


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest, principal: AuthPrincipal = Depends(get_current_principal)) -> AnalyzeResponse:
    try:
        return agent_service.analyze(
            payload,
            app_user_id=None if principal.is_development_principal else principal.id,
        )
    except AnalysisUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/analyze/stream")
async def analyze_stream(payload: AnalyzeRequest, principal: AuthPrincipal = Depends(get_current_principal)) -> StreamingResponse:
    """将真实服务阶段和最终分析结果以 SSE 发送，SQL 安全链路保持不变。"""
    owner_id = None if principal.is_development_principal else principal.id

    async def event_source():
        queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def on_stage(stage: dict[str, str]) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, ("stage", stage))

        async def run_service() -> None:
            try:
                response = await asyncio.to_thread(agent_service.analyze, payload, owner_id, on_stage)
                await queue.put(("result", response.model_dump(mode="json")))
            except AnalysisUnavailableError as exc:
                await queue.put(("error", {"status": 503, "detail": str(exc)}))
            except HTTPException as exc:
                await queue.put(("error", {"status": exc.status_code, "detail": str(exc.detail)}))
            except Exception:
                # 不向普通用户暴露服务端异常、SQL 或内部上下文。
                await queue.put(("error", {"status": 500, "detail": "分析服务暂时不可用，请稍后重试。"}))
            finally:
                await queue.put(("done", {}))

        task = asyncio.create_task(run_service())
        try:
            while True:
                event, data = await queue.get()
                yield _sse_event(event, data)
                if event == "done":
                    break
        finally:
            # 浏览器断开只停止 SSE 等待；已提交的只读分析继续受既有超时控制。
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"
