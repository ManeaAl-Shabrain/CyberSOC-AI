from typing import Protocol

class AIProvider(Protocol):
    def analyze(self, event: dict) -> dict: ...

class MockProvider:
    def analyze(self, event: dict) -> dict:
        return {"finding": "Requires analyst review", "unverified": True, "provider": "mock"}

class FoundryProvider:
    def analyze(self, event: dict) -> dict:
        raise RuntimeError("Foundry integration is disabled until region, quota, and credentials are verified")
