import logging
import os
import time
from typing import Any
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

try:
    from backend.llm.config import OpenRouterConfig
except ModuleNotFoundError:
    from llm.config import OpenRouterConfig

logger = logging.getLogger(__name__)


class LLMServiceError(RuntimeError):
    def __init__(self, message: str, code: str = 'AI_SERVICE_ERROR', details: str = ''):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        return {
            'error': True,
            'code': self.code,
            'message': self.message,
            'details': self.details
        }


class LLMClient:
    def __init__(self, config: OpenRouterConfig | None = None):
        self.config = config or OpenRouterConfig.from_environment()
        if not self.config.api_key:
            raise LLMServiceError(
                message='OpenRouter API key is missing. Please configure OPENROUTER_API_KEY on the backend server.',
                code='MISSING_API_KEY',
                details='OPENROUTER_API_KEY environment variable is not set.'
            )
        headers = {'X-Title': self.config.app_name}
        if self.config.site_url:
            headers['HTTP-Referer'] = self.config.site_url

        timeout = float(os.getenv('LLM_TIMEOUT_SECONDS', '12'))
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url='https://openrouter.ai/api/v1',
            default_headers=headers,
            timeout=timeout
        )

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        for attempt in range(2):
            try:
                kwargs: dict[str, Any] = {
                    'model': self.config.model,
                    'messages': messages,
                }
                if tools:
                    kwargs['tools'] = tools
                    kwargs['tool_choice'] = 'auto'
                
                return self.client.chat.completions.create(**kwargs)

            except APIStatusError as exc:
                status = exc.status_code
                if status == 429 and attempt == 0:
                    logger.warning('OpenRouter 429 rate limit hit. Retrying once after delay...')
                    time.sleep(1.0)
                    continue

                if status == 401:
                    logger.error('OpenRouter authentication failed (401 invalid API key).')
                    raise LLMServiceError(
                        message='Invalid OpenRouter API key provided.',
                        code='INVALID_API_KEY',
                        details='OpenRouter returned 401 Unauthorized. Check backend OPENROUTER_API_KEY configuration.'
                    ) from exc
                elif status == 403:
                    logger.error('OpenRouter access forbidden (403).')
                    raise LLMServiceError(
                        message='Access to the requested OpenRouter model or resource was forbidden.',
                        code='FORBIDDEN_ACCESS',
                        details=f'OpenRouter returned 403 Forbidden for model {self.config.model}.'
                    ) from exc
                elif status == 429:
                    logger.error('OpenRouter rate limit exceeded (429).')
                    raise LLMServiceError(
                        message='OpenRouter rate limit exceeded. Please wait a moment and try again.',
                        code='RATE_LIMIT_EXCEEDED',
                        details='OpenRouter returned 429 Rate Limit Exceeded.'
                    ) from exc
                elif status in (500, 502, 503, 504):
                    logger.error('OpenRouter server/up-stream error status=%s', status)
                    raise LLMServiceError(
                        message=f'OpenRouter upstream AI provider error (HTTP {status}).',
                        code='AI_PROVIDER_ERROR',
                        details=f'OpenRouter API returned server status {status}.'
                    ) from exc
                else:
                    logger.error('OpenRouter API HTTP error status=%s', status)
                    raise LLMServiceError(
                        message=f'OpenRouter request failed with HTTP status {status}.',
                        code='AI_API_ERROR',
                        details=f'OpenRouter HTTP error {status}.'
                    ) from exc

            except APITimeoutError as exc:
                logger.warning('OpenRouter API request timed out.')
                raise LLMServiceError(
                    message='The AI service timed out while generating a response. Please try again.',
                    code='AI_TIMEOUT',
                    details='OpenRouter request exceeded timeout threshold.'
                ) from exc

            except APIConnectionError as exc:
                logger.warning('OpenRouter API connection failed.')
                raise LLMServiceError(
                    message='Unable to connect to OpenRouter AI service. Check network connection.',
                    code='CONNECTION_FAILURE',
                    details='OpenRouter API network connection failed.'
                ) from exc

            except Exception as exc:
                logger.exception('Unexpected OpenRouter completion failure: %s', exc)
                raise LLMServiceError(
                    message='The AI service returned an unexpected response.',
                    code='MALFORMED_RESPONSE',
                    details=f'Unexpected error: {type(exc).__name__}'
                ) from exc

        raise LLMServiceError(
            message='The AI service request could not be completed.',
            code='AI_SERVICE_UNAVAILABLE',
            details='Max retry attempts exhausted.'
        )
