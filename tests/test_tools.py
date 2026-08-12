from backend.database.demo import ensure_demo_database
ensure_demo_database()
from backend.tools.schema_tool import get_schema
from backend.tools.query_tool import execute_query
from backend.tools.chart_tool import generate_chart
from backend.tools.flowchart_tool import generate_er_diagram
def test_schema_discovery(): assert 'customers' in get_schema()['tables']
def test_valid_select(): assert execute_query('SELECT * FROM customers')['success']
def test_reject_delete(): assert not execute_query('DELETE FROM customers')['success']
def test_reject_drop(): assert not execute_query('DROP TABLE customers')['success']
def test_query_execution(): assert execute_query('SELECT name FROM products')['row_count'] > 0
def test_empty_result(): assert execute_query('SELECT * FROM products WHERE id=-1')['row_count'] == 0
def test_chart_configuration(): assert generate_chart([{'name':'A','value':1}])['type'] == 'bar'
def test_mermaid_generation(): assert generate_er_diagram(get_schema()).startswith('erDiagram')
