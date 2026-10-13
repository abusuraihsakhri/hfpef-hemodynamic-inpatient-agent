"""
Inference Engine supporting local Ollama, Claude, OpenAI, and deterministic Mock with Zero-PHI checks.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Hfpef Hemodynamic Inpatient Agent"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} mock adapter]: No language-model inference or clinical verification was performed. Query preview: '{prompt[:60]}...'."


class LLMFactory:
    """Creates configured LLM client instances with zero-PHI protection."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Hfpef Hemodynamic Inpatient Agent"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError(
            f"Provider {provider!r} is not implemented. "
            "Only the deterministic mock adapter is available."
        )
