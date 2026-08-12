"""Manual OpenRouter tool-call test. Requires OPENROUTER_API_KEY in .env."""
from dotenv import load_dotenv
from backend.llm.client import LLMClient
from backend.agent.agent import TOOL_DEFINITIONS

load_dotenv()
print('=' * 50 + '\nOPENROUTER TOOL TEST\n' + '=' * 50)
try:
    client=LLMClient(); print(f'\nAPI key loaded: YES\nModel: {client.config.model}\n\nSending request...')
    response=client.complete([{'role':'system','content':'Use get_schema for database structure questions.'},{'role':'user','content':'What tables exist in my database?'}], TOOL_DEFINITIONS)
    calls=response.choices[0].message.tool_calls or []
    print('\nActual model:\n' + str(response.model)); print('\nTool calls:\n' + '\n'.join(c.function.name for c in calls))
    print('\nSUCCESS' if any(c.function.name == 'get_schema' for c in calls) else '\nNo tool call was returned by this routed model.')
except Exception as exc: print(f'\nNOT RUN / FAILED: {exc}')
