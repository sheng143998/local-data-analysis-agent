import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.main import app


client = TestClient(app)

health = client.get("/api/health")
assert health.status_code == 200, health.text

analysis = client.post("/api/analyze", json={"question": "最近 30 天销售额按天变化如何？"})
assert analysis.status_code == 200, analysis.text
body = analysis.json()
assert "SQL Guard" in body["source"]["security"]
assert body["rows"]

print("backend smoke passed: question -> FastAPI -> AgentService -> Guard -> Executor -> result")
