from uuid import uuid4

from backend.app.services.memory_service import MemoryService


class _Repository:
    def __init__(self):
        self.updated = None

    def update_trust_status(self, memory_id, trust_status):
        self.updated = (memory_id, trust_status)
        return {"id": memory_id, "trust_status": trust_status}


def test_memory_service_promotes_verified_status() -> None:
    repository = _Repository()
    result = MemoryService(repository=repository).update_trust_status(uuid4(), "verified")
    assert result["trust_status"] == "verified"
    assert repository.updated[1] == "verified"
