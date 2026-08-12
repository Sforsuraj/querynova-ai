try:
    from backend.llm.client import LLMClient, LLMServiceError
except ModuleNotFoundError:
    from llm.client import LLMClient, LLMServiceError

__all__ = ['LLMClient', 'LLMServiceError']
