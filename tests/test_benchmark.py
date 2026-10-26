import json
import sys
import types
import numpy as np
import pytest
from benchmarks.run import baseline_class, frozen_tasks, statistics
from benchmarks.human import schedule, summarize
from fixops.knowledge import load_runbooks
from fixops.retrieval import Retriever


@pytest.mark.parametrize('query',[None,123,False,{},[],b'HTTP 500','', '  ', 'x'*3001])
def test_malformed_input(query):
    with pytest.raises(ValueError,match='incident description'):
        Retriever(load_runbooks(),'tfidf').search(query)


@pytest.mark.parametrize('backend',['tfidf','semantic'])
def test_normalized_dot_equivalence(backend,monkeypatch):
    if backend=='semantic':
        class Encoder:
            def __init__(self,*args,**kwargs): pass
            def encode(self,texts,**kwargs):
                # Deterministic normalized dense fixture exercises semantic matrix path,
                # not a substitute for the real downloaded-model integration test.
                vectors = np.array([[len(t),sum(map(ord,t))%101,1] for t in texts],dtype=float)
                return vectors/np.linalg.norm(vectors,axis=1,keepdims=True)
        monkeypatch.setitem(sys.modules,'sentence_transformers',types.SimpleNamespace(SentenceTransformer=Encoder))
    docs=load_runbooks()
    old=baseline_class()(docs,backend)
    new=Retriever.__new__(Retriever)
    new.__dict__.update(old.__dict__)
    for task in frozen_tasks():
        a,b=old.search(task['query']),new.search(task['query'])
        assert [h.doc['id'] for h in a.hits]==[h.doc['id'] for h in b.hits]
        assert a.supported==b.supported
        np.testing.assert_allclose([h.score for h in a.hits],[h.score for h in b.hits],atol=1e-6)


def test_zero_vector_and_stable_ties():
    engine=Retriever(load_runbooks(),'tfidf')
    result=engine.search('zzzyyyxxx')
    assert not result.supported
    assert [h.doc['id'] for h in result.hits]==[d['id'] for d in load_runbooks()[:3]]
    assert all(h.score==0 for h in result.hits)


def test_freeze_and_answer_keys():
    docs={d['id']:d for d in load_runbooks()}
    tasks=frozen_tasks()
    assert len(tasks)==28
    for task in tasks:
        for source,steps in task['expected_resolution_steps'].items():
            assert [s['text'] for s in steps]==docs[source]['steps']
            assert task['human_required_step_numbers'][source]==[1,2,3]


def test_counterbalancing():
    rows=schedule(['A','B','C','D'],frozen_tasks())
    assert len(rows)==88
    for participant in ['A','B','C','D']:
        selected=[r for r in rows if r['participant']==participant]
        assert len({r['task_id'] for r in selected})==22
        assert sum(r['mode']=='manual' for r in selected)==11
    for task in [t for t in frozen_tasks() if t['supported']]:
        selected=[r for r in rows if r['task_id']==task['id']]
        assert sum(r['mode']=='manual' for r in selected)==2
    with pytest.raises(ValueError):schedule(['A','A'],frozen_tasks())


def test_empty_human_study_stays_unexecuted():
    assert summarize([])['status']=='unexecuted'


def test_unassessed_or_invalid_human_data_rejected():
    row=dict(participant='fixture',task_id='Q-001',mode='manual',locate_seconds='2',elapsed_seconds='3',timed_out='0',success='',errors='0',assessor='')
    with pytest.raises(ValueError):summarize([row])
    for elapsed in ['nan','inf','-1']:
        with pytest.raises(ValueError):summarize([{**row,'success':'1','assessor':'test','elapsed_seconds':elapsed}])


def test_automated_summary_denominators():
    rows=[dict(expected_supported=True,elapsed_ms=1,recall_at_1=1,recall_at_3=1,accepted=True),
          dict(expected_supported=True,elapsed_ms=3,recall_at_1=0,recall_at_3=1,accepted=False),
          dict(expected_supported=False,elapsed_ms=5,recall_at_1='',recall_at_3='',accepted=False)]
    result=statistics(rows)
    assert result['median_ms']==3
    assert result['recall_at_1']==0.5
    assert result['recall_at_3']==1
    assert result['supported_acceptance_rate']==0.5
    assert result['unsupported_rejection_rate']==1


def test_failed_human_tasks_excluded_from_success_time_but_counted():
    # Explicit synthetic test fixture; never written as study evidence.
    base=dict(participant='TEST_ONLY',task_id='Q-001',mode='manual',locate_seconds='1',elapsed_seconds='2',timed_out='0',success='1',errors='0',assessor='test')
    failed={**base,'task_id':'Q-002','elapsed_seconds':'301','timed_out':'1','success':'0','errors':'3'}
    result=summarize([base,failed])['modes']['manual']
    assert result['success_rate']==0.5
    assert result['timeouts']==1
    assert result['successful_median_seconds']==2
