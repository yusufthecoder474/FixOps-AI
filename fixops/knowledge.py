import json
from .config import ROOT

def load_runbooks(path=ROOT / 'data/runbooks.json'):
    docs = json.loads(path.read_text(encoding='utf-8'))
    ids = [d['id'] for d in docs]
    if len(ids) != len(set(ids)) or len(docs) < 20:
        raise ValueError('Runbooks require unique IDs and at least 20 entries.')
    for d in docs:
        if not d['steps'] or not d['references']:
            raise ValueError('Each runbook needs procedures and references.')
    return docs

def document_text(doc):
    return ' '.join([doc['title'], doc['tags'], doc['symptoms'], *doc['steps']])
