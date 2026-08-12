import json
from types import SimpleNamespace
from backend.agent.agent import DataAnalystAgent

def test_registry_only_exposes_expected_tools():
    state={}; assert set(DataAnalystAgent()._tool_registry(state)) == {'get_schema','execute_query','generate_chart','generate_flowchart','explain_data'}

def test_tool_call_loop_executes_schema(monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY','test-key')
    call=SimpleNamespace(id='call_1', function=SimpleNamespace(name='get_schema', arguments='{}'), model_dump=lambda:{'id':'call_1','type':'function','function':{'name':'get_schema','arguments':'{}'}})
    tool_message=SimpleNamespace(tool_calls=[call], content=None)
    final_message=SimpleNamespace(tool_calls=[], content='The database contains customers and orders.')
    completions=[SimpleNamespace(choices=[SimpleNamespace(message=tool_message)],model='test-model'),SimpleNamespace(choices=[SimpleNamespace(message=final_message)],model='test-model')]
    class FakeClient:
        def __init__(self,*_): pass
        def complete(self,*_): return completions.pop(0)
    monkeypatch.setattr('backend.agent.agent.LLMClient',FakeClient)
    response=DataAnalystAgent().respond('What tables exist?', 'test')
    assert response['message'].startswith('The database')
    assert response['tool_calls'] == [{'tool':'get_schema'}]
