"""Reproducible warm retrieval evaluation; never substitutes engines silently."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from time import perf_counter
import numpy as np
from fixops.config import ROOT, Settings
from fixops.knowledge import load_runbooks
from fixops.retrieval import Retriever

def evaluate(backend, questions, docs, settings):
    start = perf_counter()
    threshold = settings.semantic_threshold if backend == 'semantic' else settings.tfidf_threshold
    engine = Retriever(docs, backend, settings.model, threshold)
    startup = (perf_counter() - start)*1000
    engine.search('HTTP 500 application error')  # Warm up; excluded from latency.
    rows = []
    for q in questions:
        result = engine.search(q['query'])
        ids = [h.doc['id'] for h in result.hits]
        expected = set(q['expected_sources'])
        recall = len(expected.intersection(ids))/len(expected) if expected else None
        rows.append({'id': q['id'], 'expected': sorted(expected), 'retrieved': ids,
                     'recall_at_3': recall, 'expected_supported': q['supported'],
                     'accepted': result.supported, 'latency_ms': result.latency_ms})
    supported = [r for r in rows if r['expected_supported']]
    unsupported = [r for r in rows if not r['expected_supported']]
    times = [r['latency_ms'] for r in rows]
    return {'status': 'measured', 'backend': backend, 'threshold': threshold,
            'startup_ms': startup,
            'recall_at_3': float(np.mean([r['recall_at_3'] for r in supported])),
            'supported_acceptance_rate': float(np.mean([r['accepted'] for r in supported])),
            'unsupported_rejection_rate': float(np.mean([not r['accepted'] for r in unsupported])),
            'latency_mean_ms': float(np.mean(times)), 'latency_p50_ms': float(np.percentile(times, 50)),
            'latency_p95_ms': float(np.percentile(times, 95)), 'questions': rows}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', choices=['both', 'semantic', 'tfidf'], default='both')
    parser.add_argument('--output', default='reports/evaluation.json')
    args = parser.parse_args()
    settings = Settings()
    questions = json.loads((ROOT / 'data/evaluation.json').read_text())
    versions = {}
    for package in ['numpy', 'scikit-learn', 'sentence-transformers', 'streamlit']:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = 'not installed'
    report = {'timestamp': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(),
              'platform': platform.platform(), 'versions': versions, 'model': settings.model,
              'dataset_sha256': hashlib.sha256((ROOT / 'data/runbooks.json').read_bytes()).hexdigest(),
              'evaluation_sha256': hashlib.sha256((ROOT / 'data/evaluation.json').read_bytes()).hexdigest(),
              'method': 'Macro Recall@3 over 22 supported questions; 6 unsupported excluded from recall. One warm timed request per question including query encoding, cosine ranking and scope check; no UI/LLM/network time. Startup measured separately. Authored smoke set, not an independent benchmark.',
              'results': []}
    for backend in (['tfidf', 'semantic'] if args.backend == 'both' else [args.backend]):
        try:
            result = evaluate(backend, questions, load_runbooks(), settings)
        except Exception as exc:
            result = {'backend': backend, 'status': 'unavailable', 'error_type': type(exc).__name__,
                      'note': 'Install dependencies and download/cache the configured model, then rerun. No metric fabricated.'}
        report['results'].append(result)
        print(json.dumps({k: v for k, v in result.items() if k != 'questions'}, indent=2))
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    if any(r['status'] != 'measured' for r in report['results']):
        raise SystemExit(2)

if __name__ == '__main__':
    main()
