import logging, time
from typing import Any
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI
from backend.llm.config import OpenRouterConfig

logger = logging.getLogger(__name__)
class LLMServiceError(RuntimeError): pass

class LLMClient:
    def __init__(self, config: OpenRouterConfig | None = None):
        self.config = config or OpenRouterConfig.from_environment()
        if not self.config.api_key: raise ValueError('OPENROUTER_API_KEY is not configured')
        headers = {'X-Title': self.config.app_name}
        if self.config.site_url: headers['HTTP-Referer'] = self.config.site_url
        self.client = OpenAI(api_key=self.config.api_key, base_url='https://openrouter.ai/api/v1', default_headers=headers, timeout=20.0)

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]):
        for attempt in range(2):
            try: return self.client.chat.completions.create(model=self.config.model, messages=messages, tools=tools, tool_choice='auto')
            except APIStatusError as exc:
                if exc.status_code == 429 and attempt == 0: time.sleep(0.5); continue
                logger.warning('OpenRouter request failed with status %s', exc.status_code)
                raise LLMServiceError('The AI service is temporarily unavailable. Please try again in a moment.') from exc
            except (APIConnectionError, APITimeoutError) as exc:
                logger.warning('OpenRouter network failure: %s', type(exc).__name__)
                raise LLMServiceError('The AI service is temporarily unavailable. Please try again in a moment.') from exc
            except Exception as exc:
                logger.exception('Unexpected OpenRouter client failure')
                raise LLMServiceError('The AI service returned an invalid response. Please try again.') from exc
        raise LLMServiceError('The AI service is temporarily unavailable. Please try again in a moment.')
