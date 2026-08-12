"""Manual OpenRouter connectivity test. Requires OPENROUTER_API_KEY in .env."""
from dotenv import load_dotenv
from backend.llm.client import LLMClient

load_dotenv()
print('=' * 50 + '\nOPENROUTER TEST\n' + '=' * 50)
try:
    client=LLMClient(); print(f'\nAPI key loaded: YES\nModel: {client.config.model}\n\nSending request...')
    response=client.complete([{'role':'user','content':'Reply with exactly: OPENROUTER WORKING'}], [])
    print('\nSUCCESS\n\nResponse:\n' + (response.choices[0].message.content or ''))
    print('\nActual model:\n' + str(response.model)); print('\nToken usage:\n' + str(response.usage))
except Exception as exc: print(f'\nNOT RUN / FAILED: {exc}')
