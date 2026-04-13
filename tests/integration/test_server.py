# tests/integration/test_server.py
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import json
from backend.ppt.liveppt_server import app, init_pipeline

@pytest.fixture
def client():
    app.config['TESTING'] = True
    init_pipeline()
    with app.test_client() as client:
        yield client

def test_health_check(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'ok'

def test_wiki_list(client):
    rv = client.get('/api/wiki/list')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'sources' in data or 'entities' in data
