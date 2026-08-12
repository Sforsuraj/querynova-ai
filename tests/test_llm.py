import pytest
from backend.llm.client import LLMClient, LLMServiceError
from backend.llm.config import OpenRouterConfig

def test_openrouter_requires_key():
    with pytest.raises(LLMServiceError) as exc_info:
        LLMClient(OpenRouterConfig('', 'openrouter/free', '', 'QueryNova'))
    assert exc_info.value.code == 'MISSING_API_KEY'

def test_openrouter_configuration_defaults(monkeypatch):
    monkeypatch.delenv('OPENROUTER_MODEL', raising=False)
    assert OpenRouterConfig.from_environment().model == 'openrouter/free'
    assert OpenRouterConfig.from_environment().app_name == 'QueryNova'
