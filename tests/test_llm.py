import pytest
from backend.llm.client import LLMClient
from backend.llm.config import OpenRouterConfig

def test_openrouter_requires_key():
    with pytest.raises(ValueError, match='OPENROUTER_API_KEY'):
        LLMClient(OpenRouterConfig('', 'openrouter/free', '', 'QueryNova AI'))

def test_openrouter_configuration_defaults(monkeypatch):
    monkeypatch.delenv('OPENROUTER_MODEL', raising=False)
    assert OpenRouterConfig.from_environment().model == 'openrouter/free'
