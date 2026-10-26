import json
import os
from dataclasses import replace
from pathlib import Path
import pytest
from fixops.config import ROOT, Settings
from fixops.knowledge import load_runbooks
from fixops.retrieval import Retriever
from fixops.history import History
from fixops.answer import answer, validate_selection
from fixops.privacy import redact, query_summary

@pytest.fixture(scope='module')
def docs():
    return load_runbooks()

@pytest.fixture(scope='module')
def engine(docs):
    return Retriever(docs, 'tfidf')

def test_dataset_integrity(docs):
    assert len(docs) >= 20
    questions = json.loads((ROOT / 'data/evaluation.json').read_text())
    assert len(questions) >= 20
    ids = {d['id'] for d in docs}
    assert all(set(q['expected_sources']) <= ids for q in questions)

@pytest.mark.parametrize('question', json.loads((ROOT / 'data/evaluation.json').read_text()))
def test_baseline_retrieval(engine, question):
    result = engine.search(question['query'])
    assert len(result.hits) == 3
    assert [h.score for h in result.hits] == sorted([h.score for h in result.hits], reverse=True)
    if question['supported']:
        assert set(question['expected_sources']) & {h.doc['id'] for h in result.hits}
        assert result.supported
    else:
        assert not result.supported

@pytest.mark.parametrize('query', ['', '   ', 'x'*3001])
def test_validation(engine, query):
    with pytest.raises(ValueError):
        engine.search(query)

def test_history_stores_no_raw_text(engine, tmp_path):
    query = 'CPU high password=hunter2 Authorization: Bearer abcdefghijklmnop https://user:secret@example.org arbitrarySecretNotMatchingRegex'
    history = History(tmp_path / 'history.sqlite3')
    history.add(query, engine.search(query))
    raw = history.path.read_bytes()
    for secret in ['hunter2', 'abcdefghijklmnop', 'user:secret', 'arbitrarySecretNotMatchingRegex']:
        assert secret.encode() not in raw
    assert history.recent()[0]['query_summary'] == 'cpu'

def test_history_retention(engine, tmp_path):
    history = History(tmp_path / 'history.sqlite3')
    result = engine.search('CPU high')
    for _ in range(105):
        history.add('CPU high', result)
    with history.connect() as db:
        assert db.execute('SELECT count(*) FROM history').fetchone()[0] == 100

def test_local_answer_and_abstention(engine):
    steps, _ = answer(engine.search('HTTP 500'), 'HTTP 500', Settings())
    assert len(steps) == 3 and all('[RB-' in s for s in steps)
    steps, _ = answer(engine.search('Bake a cake'), 'Bake a cake', Settings())
    assert steps == []

def test_invalid_citations_rejected(engine):
    hits = engine.search('HTTP 500').hits
    for payload in [{'steps': [{'source':'RB-999','step':1}]},
                    {'steps': [{'source':hits[0].doc['id'],'step':0}]},
                    {'steps': [{'source':hits[0].doc['id'],'step':True}]},
                    {'steps': [{'source':hits[0].doc['id'],'step':1,'command':'delete'}]},
                    {'steps': []}]:
        with pytest.raises(ValueError):
            validate_selection(payload, hits)

def test_valid_citation_is_exact_extract(engine):
    hits = engine.search('HTTP 500').hits
    selected = validate_selection({'steps':[{'source':hits[0].doc['id'],'step':2}]}, hits)
    assert selected[0].startswith(hits[0].doc['steps'][1])

def test_llm_failure_falls_back_without_leaking(engine, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('TOP_SECRET_PROVIDER_PAYLOAD')
    monkeypatch.setattr('urllib.request.OpenerDirector.open', fail)
    settings = replace(Settings(), api_key='fake', llm_model='test')
    steps, notice = answer(engine.search('HTTP 500'), 'HTTP 500', settings, True)
    assert steps and 'TOP_SECRET' not in notice

def test_llm_valid_response_and_outbound_privacy(engine, monkeypatch):
    result = engine.search('HTTP 500')
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, limit):
            content = json.dumps({'steps':[{'source':result.hits[0].doc['id'],'step':1}]})
            return json.dumps({'choices':[{'message':{'content':content}}]}).encode()
    def fake_open(self, request, timeout):
        assert b'unknown-secret-string' not in request.data
        return Response()
    monkeypatch.setattr('urllib.request.OpenerDirector.open', fake_open)
    steps, notice = answer(result, 'HTTP 500 unknown-secret-string', replace(Settings(), api_key='fake', llm_model='test'), True)
    assert len(steps) == 1 and 'LLM-selected' in notice

def test_http_endpoint_rejected(engine):
    steps, notice = answer(engine.search('HTTP 500'), 'HTTP 500', replace(Settings(), api_key='fake', llm_model='test', api_url='http://example.org'), True)
    assert steps and 'HTTPS' in notice

def test_redaction():
    assert 'hunter2' not in redact('password=hunter2')
    assert query_summary('random unknown secret') == 'unclassified incident'

@pytest.mark.semantic
@pytest.mark.skipif(os.getenv('FIXOPS_TEST_SEMANTIC') != '1', reason='Enable real downloaded-model integration explicitly')
def test_real_semantic_model(docs):
    engine = Retriever(docs, 'semantic')
    questions = json.loads((ROOT / 'data/evaluation.json').read_text())
    supported = [q for q in questions if q['supported']]
    hits = sum(bool(set(q['expected_sources']) & {h.doc['id'] for h in engine.search(q['query']).hits}) for q in supported)
    assert hits / len(supported) >= 0.85
    for q in questions:
        if not q['supported']:
            assert not engine.search(q['query']).supported

def test_settings_read_environment_at_instance_creation(monkeypatch, tmp_path):
    monkeypatch.setenv('FIXOPS_MODEL', 'first-model')
    first = Settings()
    monkeypatch.setenv('FIXOPS_MODEL', 'second-model')
    monkeypatch.setenv('FIXOPS_HISTORY_PATH', str(tmp_path / 'custom.sqlite3'))
    second = Settings()
    assert first.model == 'first-model'
    assert second.model == 'second-model'
    assert second.history_path == tmp_path / 'custom.sqlite3'

@pytest.mark.parametrize('value', ['0', '1.1', 'nan'])
def test_invalid_threshold_configuration(monkeypatch, value):
    monkeypatch.setenv('FIXOPS_SEMANTIC_THRESHOLD', value)
    with pytest.raises(ValueError):
        Settings()
